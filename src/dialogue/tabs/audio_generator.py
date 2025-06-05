"""Audio generator tab for creating dialogue audio."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.services import APIService
from src.utils.audio import AudioPlayer


class AudioGeneratorTab(QWidget):
    """Tab for generating audio from dialogue scripts."""
    
    generation_complete = pyqtSignal(str)  # Path to generated audio
    
    def __init__(self, api_service: APIService):
        super().__init__()
        self.api_service = api_service
        self.logger = logging.getLogger(__name__)
        
        self.current_dialogue: Optional[Dict] = None
        self.generated_audio_path: Optional[str] = None
        self.voice_profiles: List[Dict] = []
        self.audio_player = AudioPlayer()
        self._pending_dialogue = False
        
        # Audio generation state
        self.is_generating = False
        self.generation_progress = 0
        self.total_lines = 0
        
        self.init_ui()
        self.load_voice_profiles()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Dialogue preview
        preview_group = QGroupBox("Dialogue Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.dialogue_preview = QTextEdit()
        self.dialogue_preview.setReadOnly(True)
        self.dialogue_preview.setMaximumHeight(150)
        preview_layout.addWidget(self.dialogue_preview)
        
        layout.addWidget(preview_group)
        
        # Voice selection
        voice_group = QGroupBox("Voice Selection")
        voice_layout = QVBoxLayout(voice_group)
        
        # Speaker A
        speaker_a_layout = QHBoxLayout()
        self.speaker_a_label = QLabel("Speaker A:")
        self.speaker_a_label.setMinimumWidth(100)
        speaker_a_layout.addWidget(self.speaker_a_label)
        
        self.voice_a_combo = QComboBox()
        self.voice_a_combo.setToolTip("Select voice for Speaker A")
        speaker_a_layout.addWidget(self.voice_a_combo, 1)
        
        self.refresh_voices_btn = QPushButton("🔄")
        self.refresh_voices_btn.setToolTip("Refresh voice list")
        self.refresh_voices_btn.setMaximumWidth(30)
        self.refresh_voices_btn.clicked.connect(self.load_voice_profiles)
        speaker_a_layout.addWidget(self.refresh_voices_btn)
        
        voice_layout.addLayout(speaker_a_layout)
        
        # Speaker B
        speaker_b_layout = QHBoxLayout()
        self.speaker_b_label = QLabel("Speaker B:")
        self.speaker_b_label.setMinimumWidth(100)
        speaker_b_layout.addWidget(self.speaker_b_label)
        
        self.voice_b_combo = QComboBox()
        self.voice_b_combo.setToolTip("Select voice for Speaker B")
        speaker_b_layout.addWidget(self.voice_b_combo, 1)
        
        voice_layout.addLayout(speaker_b_layout)
        
        layout.addWidget(voice_group)
        
        # Voice parameters
        params_group = QGroupBox("Voice Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # Speaker A parameters
        speaker_a_params = QGroupBox("Speaker A Settings")
        speaker_a_params_layout = QHBoxLayout(speaker_a_params)
        
        speaker_a_params_layout.addWidget(QLabel("Speed:"))
        self.speed_a_spin = QDoubleSpinBox()
        self.speed_a_spin.setRange(0.5, 2.0)
        self.speed_a_spin.setSingleStep(0.1)
        self.speed_a_spin.setValue(1.0)
        self.speed_a_spin.setSuffix("x")
        speaker_a_params_layout.addWidget(self.speed_a_spin)
        
        speaker_a_params_layout.addWidget(QLabel("Pitch:"))
        self.pitch_a_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_a_slider.setRange(-50, 50)
        self.pitch_a_slider.setValue(0)
        self.pitch_a_slider.setMaximumWidth(100)
        speaker_a_params_layout.addWidget(self.pitch_a_slider)
        self.pitch_a_label = QLabel("0")
        self.pitch_a_label.setMinimumWidth(30)
        speaker_a_params_layout.addWidget(self.pitch_a_label)
        self.pitch_a_slider.valueChanged.connect(lambda v: self.pitch_a_label.setText(str(v)))
        
        speaker_a_params_layout.addWidget(QLabel("Emotion:"))
        self.emotion_a_combo = QComboBox()
        self.emotion_a_combo.addItems(["Neutral", "Happy", "Sad", "Angry", "Surprised"])
        speaker_a_params_layout.addWidget(self.emotion_a_combo)
        
        speaker_a_params_layout.addStretch()
        params_layout.addWidget(speaker_a_params)
        
        # Speaker B parameters
        speaker_b_params = QGroupBox("Speaker B Settings")
        speaker_b_params_layout = QHBoxLayout(speaker_b_params)
        
        speaker_b_params_layout.addWidget(QLabel("Speed:"))
        self.speed_b_spin = QDoubleSpinBox()
        self.speed_b_spin.setRange(0.5, 2.0)
        self.speed_b_spin.setSingleStep(0.1)
        self.speed_b_spin.setValue(1.0)
        self.speed_b_spin.setSuffix("x")
        speaker_b_params_layout.addWidget(self.speed_b_spin)
        
        speaker_b_params_layout.addWidget(QLabel("Pitch:"))
        self.pitch_b_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_b_slider.setRange(-50, 50)
        self.pitch_b_slider.setValue(0)
        self.pitch_b_slider.setMaximumWidth(100)
        speaker_b_params_layout.addWidget(self.pitch_b_slider)
        self.pitch_b_label = QLabel("0")
        self.pitch_b_label.setMinimumWidth(30)
        speaker_b_params_layout.addWidget(self.pitch_b_label)
        self.pitch_b_slider.valueChanged.connect(lambda v: self.pitch_b_label.setText(str(v)))
        
        speaker_b_params_layout.addWidget(QLabel("Emotion:"))
        self.emotion_b_combo = QComboBox()
        self.emotion_b_combo.addItems(["Neutral", "Happy", "Sad", "Angry", "Surprised"])
        speaker_b_params_layout.addWidget(self.emotion_b_combo)
        
        speaker_b_params_layout.addStretch()
        params_layout.addWidget(speaker_b_params)
        
        layout.addWidget(params_group)
        
        # Dialogue settings
        dialogue_settings = QGroupBox("Dialogue Settings")
        dialogue_layout = QHBoxLayout(dialogue_settings)
        
        dialogue_layout.addWidget(QLabel("Pause Between Speakers:"))
        self.pause_spin = QDoubleSpinBox()
        self.pause_spin.setRange(0.0, 5.0)
        self.pause_spin.setSingleStep(0.1)
        self.pause_spin.setValue(0.5)
        self.pause_spin.setSuffix(" seconds")
        dialogue_layout.addWidget(self.pause_spin)
        
        dialogue_layout.addStretch()
        
        layout.addWidget(dialogue_settings)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to generate audio")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎵 Generate Audio")
        self.generate_btn.clicked.connect(self.generate)
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        self.preview_btn = QPushButton("▶️ Preview")
        self.preview_btn.clicked.connect(self.preview)
        self.preview_btn.setEnabled(False)
        button_layout.addWidget(self.preview_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.export_audio)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def load_voice_profiles(self) -> None:
        """Load available voice profiles."""
        if not self.api_service.client:
            self.logger.warning("API service not connected, retrying in 500ms...")
            QTimer.singleShot(500, self.load_voice_profiles)
            return
            
        async def load():
            try:
                profiles = await self.api_service.client.list_voice_profiles()
                self.logger.info(f"Loaded {len(profiles)} voice profiles")
                # Only show cloned voices
                cloned = [p for p in profiles if p.get("is_cloned", False)]
                self.logger.info(f"Found {len(cloned)} cloned voices")
                return cloned
            except Exception as e:
                self.logger.error(f"Failed to load voice profiles: {e}")
                return []
                
        future = self.api_service.run_async(load())
        
        def check_result():
            if future.done():
                try:
                    self.voice_profiles = future.result()
                    self.update_voice_combos()
                except Exception as e:
                    self.logger.error(f"Error loading voices: {e}")
                    QMessageBox.warning(self, "Error", "Failed to load voice profiles")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def update_voice_combos(self) -> None:
        """Update voice selection combos."""
        self.voice_a_combo.clear()
        self.voice_b_combo.clear()
        
        if not self.voice_profiles:
            self.voice_a_combo.addItem("No voices available")
            self.voice_b_combo.addItem("No voices available")
            return
            
        for profile in self.voice_profiles:
            self.voice_a_combo.addItem(profile["name"], profile["id"])
            self.voice_b_combo.addItem(profile["name"], profile["id"])
            
        # Try to select different voices
        if len(self.voice_profiles) > 1:
            self.voice_b_combo.setCurrentIndex(1)
            
        # Enable generate button if we have a pending dialogue
        if self._pending_dialogue and self.current_dialogue:
            self.generate_btn.setEnabled(True)
            self._pending_dialogue = False
            
    def set_dialogue(self, dialogue: Dict) -> None:
        """Set dialogue to generate audio from."""
        self.current_dialogue = dialogue
        
        if not dialogue:
            self.dialogue_preview.clear()
            self.generate_btn.setEnabled(False)
            return
            
        self.logger.info(f"Setting dialogue: {dialogue.keys()}")
        
        # Update speaker labels
        speaker_a = dialogue.get("speaker_a", "Speaker A")
        speaker_b = dialogue.get("speaker_b", "Speaker B")
        self.speaker_a_label.setText(f"{speaker_a}:")
        self.speaker_b_label.setText(f"{speaker_b}:")
        
        # Update preview
        lines = dialogue.get("lines", [])
        self.logger.info(f"Dialogue has {len(lines)} lines")
        
        preview_text = []
        for i, line in enumerate(lines[:5]):  # Show first 5 lines
            preview_text.append(f"{line['speaker']}: {line['text']}")
        if len(lines) > 5:
            preview_text.append(f"... and {len(lines) - 5} more lines")
            
        self.dialogue_preview.setPlainText('\n'.join(preview_text))
        
        # Check if we need to wait for voices to load
        if not self.voice_profiles:
            self.logger.info("No voice profiles loaded, waiting for them to load...")
            self.generate_btn.setEnabled(False)
            # Store dialogue to enable button once voices are loaded
            self._pending_dialogue = True
        else:
            self.generate_btn.setEnabled(True)
            self._pending_dialogue = False
        
        self.logger.info(f"Set dialogue with {len(lines)} lines")
        
    def generate(self) -> None:
        """Generate audio from dialogue."""
        if not self.current_dialogue or self.is_generating:
            return
            
        # Check voice selection
        if self.voice_a_combo.currentData() is None or self.voice_b_combo.currentData() is None:
            QMessageBox.warning(self, "No Voices", "Please select voices for both speakers.")
            return
            
        # Disable controls during generation
        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.voice_a_combo.setEnabled(False)
        self.voice_b_combo.setEnabled(False)
        
        # Reset progress
        self.generation_progress = 0
        self.total_lines = len(self.current_dialogue.get("lines", []))
        self.progress_bar.setMaximum(self.total_lines)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Start generation
        self.status_label.setText("Generating audio...")
        
        # Get parameters
        params_a = {
            "voice_profile_id": self.voice_a_combo.currentData(),
            "speed": self.speed_a_spin.value(),
            "pitch": self.pitch_a_slider.value() / 50.0,
            "emotion": self.emotion_a_combo.currentText().lower(),
        }
        
        params_b = {
            "voice_profile_id": self.voice_b_combo.currentData(),
            "speed": self.speed_b_spin.value(),
            "pitch": self.pitch_b_slider.value() / 50.0,
            "emotion": self.emotion_b_combo.currentText().lower(),
        }
        
        pause_duration = self.pause_spin.value()
        
        # Generate audio for each line
        self.generate_dialogue_audio(params_a, params_b, pause_duration)
        
    def generate_dialogue_audio(self, params_a: Dict, params_b: Dict, pause_duration: float) -> None:
        """Generate audio for the dialogue."""
        async def generate_async():
            try:
                lines = self.current_dialogue.get("lines", [])
                speaker_a = self.current_dialogue.get("speaker_a", "Speaker A")
                speaker_b = self.current_dialogue.get("speaker_b", "Speaker B")
                
                audio_segments = []
                sample_rate = 24000  # Default sample rate
                
                for i, line in enumerate(lines):
                    # Update progress
                    self.generation_progress = i
                    
                    # Determine which voice to use
                    if line["speaker"] == speaker_a:
                        params = params_a
                    else:
                        params = params_b
                        
                    # Generate audio for this line
                    self.logger.info(f"Generating line {i+1}/{len(lines)}: {line['text'][:50]}...")
                    
                    response = await self.api_service.client._request(
                        "POST",
                        "/api/tts/generate/quick",
                        json={
                            "text": line["text"],
                            "voice_profile_id": params["voice_profile_id"],
                            "speed": params["speed"],
                            "pitch": params["pitch"],
                            "emotion": params["emotion"],
                        }
                    )
                    
                    # Get audio data
                    audio_data = response.get("audio_data", [])
                    if audio_data:
                        audio_array = np.array(audio_data, dtype=np.float32)
                        audio_segments.append(audio_array)
                        
                        # Add pause after each line (except the last)
                        if i < len(lines) - 1 and pause_duration > 0:
                            pause_samples = int(sample_rate * pause_duration)
                            pause_array = np.zeros(pause_samples, dtype=np.float32)
                            audio_segments.append(pause_array)
                            
                    # Update UI
                    self.progress_bar.setValue(i + 1)
                    self.status_label.setText(f"Generated {i + 1}/{len(lines)} lines...")
                    
                # Combine all segments
                if audio_segments:
                    combined_audio = np.concatenate(audio_segments)
                    
                    # Save to temporary file
                    from src.utils.config import get_settings
                    settings = get_settings()
                    output_dir = settings.outputs_dir / "dialogues"
                    output_dir.mkdir(exist_ok=True)
                    
                    timestamp = asyncio.get_event_loop().time()
                    output_file = output_dir / f"dialogue_{int(timestamp)}.wav"
                    
                    # Save audio
                    import soundfile as sf
                    sf.write(str(output_file), combined_audio, sample_rate)
                    
                    return str(output_file)
                    
            except Exception as e:
                self.logger.error(f"Failed to generate audio: {e}")
                raise
                
        future = self.api_service.run_async(generate_async())
        
        def check_result():
            if future.done():
                try:
                    audio_path = future.result()
                    self.on_generation_complete(audio_path)
                except Exception as e:
                    self.on_generation_error(str(e))
            else:
                QTimer.singleShot(100, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_generation_complete(self, audio_path: str) -> None:
        """Handle successful audio generation."""
        self.generated_audio_path = audio_path
        self.is_generating = False
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.status_label.setText("Audio generation complete!")
        self.generate_btn.setEnabled(True)
        self.voice_a_combo.setEnabled(True)
        self.voice_b_combo.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        self.generation_complete.emit(audio_path)
        
        # Auto-play preview
        QTimer.singleShot(500, self.preview)
        
    def on_generation_error(self, error_msg: str) -> None:
        """Handle generation error."""
        self.is_generating = False
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.status_label.setText("Generation failed")
        self.generate_btn.setEnabled(True)
        self.voice_a_combo.setEnabled(True)
        self.voice_b_combo.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Generation Error",
            f"Failed to generate audio:\n{error_msg}"
        )
        
    def preview(self) -> None:
        """Preview generated audio."""
        if not self.generated_audio_path or not os.path.exists(self.generated_audio_path):
            return
            
        try:
            with open(self.generated_audio_path, 'rb') as f:
                audio_data = f.read()
                
            if self.audio_player.play(audio_data):
                self.preview_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText("Playing audio...")
                
                # Check playback status
                QTimer.singleShot(100, self._check_playback_status)
            else:
                QMessageBox.warning(self, "Playback Error", "Failed to play audio")
                
        except Exception as e:
            self.logger.error(f"Preview error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to preview audio: {e}")
            
    def _check_playback_status(self) -> None:
        """Check if playback is still running."""
        if self.audio_player.is_playing:
            QTimer.singleShot(100, self._check_playback_status)
        else:
            self.preview_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Ready")
            
    def stop_playback(self) -> None:
        """Stop audio playback."""
        self.audio_player.stop()
        self.preview_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Playback stopped")
        
    def export_audio(self) -> None:
        """Export generated audio."""
        if not self.generated_audio_path or not os.path.exists(self.generated_audio_path):
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audio",
            f"dialogue_{self.current_dialogue.get('script_type', 'conversation')}.wav",
            "WAV Files (*.wav);;MP3 Files (*.mp3);;All Files (*.*)"
        )
        
        if filename:
            try:
                # Copy the file
                import shutil
                shutil.copy2(self.generated_audio_path, filename)
                
                self.status_label.setText(f"Exported to {Path(filename).name}")
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Audio exported successfully to:\n{filename}"
                )
            except Exception as e:
                self.logger.error(f"Export error: {e}")
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export audio:\n{e}"
                )
                
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_playback()
        # Clean up temporary files
        if self.generated_audio_path and os.path.exists(self.generated_audio_path):
            try:
                os.remove(self.generated_audio_path)
            except:
                pass