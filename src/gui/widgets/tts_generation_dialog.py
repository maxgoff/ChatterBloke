"""TTS generation dialog for generating audio from scripts."""

import asyncio
import logging
from typing import Optional, List, Any
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QComboBox,
    QSlider,
    QSpinBox,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QDialogButtonBox,
)

from src.api.models import VoiceProfileResponse
from src.gui.services import get_api_service
from src.gui.services import AsyncWorker
from src.gui.widgets.custom_widgets import ProgressDialog
from src.gui.widgets.notification import NotificationManager
from src.utils.config import get_settings
from src.utils.error_handler import handle_error
from src.utils.performance import performance_monitor


class TTSGenerationDialog(QDialog):
    """Dialog for generating TTS audio from text using cloned voices."""
    
    # Signals
    audio_generated = pyqtSignal(str)  # Emitted with file path when audio is generated
    
    def __init__(self, parent=None):
        """Initialize TTS generation dialog."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.api_service = get_api_service()
        self.notification_manager = NotificationManager.get_instance()
        
        self.voices: List[VoiceProfileResponse] = []
        self.selected_voice_id: Optional[int] = None
        self.script_text = ""
        self.suggested_filename = "generated_audio"
        self.is_connected = False
        self.is_loading_voices = False
        self.load_voices_worker: Optional[AsyncWorker] = None
        self.generate_worker: Optional[AsyncWorker] = None
        self.generated_audio_data: Optional[bytes] = None
        self.audio_player: Optional[Any] = None
        
        # Connect to API status
        self.api_service.connected.connect(self.on_api_connected)
        
        self.init_ui()
        
        # Check initial connection status by checking if client exists
        if self.api_service.client:
            self.is_connected = True
            self.load_voices()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Generate Audio from Script")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Script text input
        script_group = QGroupBox("Script Text")
        script_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter or paste your script text here...")
        self.text_edit.setMinimumHeight(200)
        script_layout.addWidget(self.text_edit)
        
        # Character count
        self.char_count_label = QLabel("Characters: 0")
        script_layout.addWidget(self.char_count_label)
        self.text_edit.textChanged.connect(self.update_char_count)
        
        # Add hint about text length
        hint_label = QLabel("💡 Tip: Keep text under 200 characters for quick results (~90s). CPU processing is slow!")
        hint_label.setStyleSheet("color: #666; font-style: italic;")
        script_layout.addWidget(hint_label)
        
        script_group.setLayout(script_layout)
        layout.addWidget(script_group)
        
        # Voice selection
        voice_group = QGroupBox("Voice Selection")
        voice_layout = QFormLayout()
        
        self.voice_combo = QComboBox()
        self.voice_combo.currentIndexChanged.connect(self.on_voice_selected)
        voice_layout.addRow("Voice:", self.voice_combo)
        
        self.voice_status_label = QLabel("No voice selected")
        voice_layout.addRow("Status:", self.voice_status_label)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        
        # TTS Parameters
        params_group = QGroupBox("TTS Parameters")
        params_layout = QFormLayout()
        
        # Speed
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(25)
        self.speed_label = QLabel("100%")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v}%"))
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        params_layout.addRow("Speed:", speed_layout)
        
        # Pitch
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pitch_slider.setTickInterval(10)
        self.pitch_label = QLabel("0")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        params_layout.addRow("Pitch:", pitch_layout)
        
        # Emotion
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["neutral", "happy", "sad", "angry", "surprised"])
        params_layout.addRow("Emotion:", self.emotion_combo)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Result section (hidden initially)
        self.result_group = QGroupBox("Generated Audio")
        result_layout = QVBoxLayout()
        
        self.result_label = QLabel("Audio generation complete!")
        result_layout.addWidget(self.result_label)
        
        result_buttons = QHBoxLayout()
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.play_generated_audio)
        self.play_button.setEnabled(False)
        result_buttons.addWidget(self.play_button)
        
        self.save_button = QPushButton("💾 Save As...")
        self.save_button.clicked.connect(self.save_generated_audio)
        self.save_button.setEnabled(False)
        result_buttons.addWidget(self.save_button)
        
        result_buttons.addStretch()
        result_layout.addLayout(result_buttons)
        
        self.result_group.setLayout(result_layout)
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        
        # Buttons
        button_box = QDialogButtonBox()
        self.generate_button = QPushButton("Generate Audio")
        self.generate_button.clicked.connect(self.generate_audio)
        button_box.addButton(self.generate_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        # Add test button for quick testing
        self.test_button = QPushButton("Test with Sample")
        self.test_button.setToolTip("Test with a short sample text")
        self.test_button.clicked.connect(self.test_with_sample)
        button_box.addButton(self.test_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        button_box.addButton(self.close_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        
        # Update initial state
        self.update_generate_button()
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status change."""
        was_connected = self.is_connected
        self.is_connected = is_connected
        
        if is_connected and not was_connected:
            # Only load voices if we're newly connected
            self.load_voices()
        elif not is_connected and was_connected:
            # Clear voices if we lost connection
            self.voice_status_label.setText("API not connected")
            self.voice_combo.clear()
            self.voice_combo.addItem("No API connection")
            
    def load_voices(self) -> None:
        """Load available voices from API."""
        self.logger.info(f"Loading voices, is_connected: {self.is_connected}, is_loading: {self.is_loading_voices}")
        
        # Prevent multiple simultaneous loads
        if self.is_loading_voices:
            self.logger.info("Already loading voices, skipping")
            return
            
        if not self.is_connected:
            self.voice_status_label.setText("API not connected")
            return
            
        self.is_loading_voices = True
        
        # Clean up previous worker if exists
        if self.load_voices_worker and self.load_voices_worker.isRunning():
            self.load_voices_worker.quit()
            self.load_voices_worker.wait()
            
        self.load_voices_worker = AsyncWorker(self._load_voices)
        self.load_voices_worker.result.connect(self._on_voices_loaded)
        self.load_voices_worker.error.connect(self._on_load_error)
        self.load_voices_worker.finished.connect(lambda: self._cleanup_worker('load_voices'))
        self.load_voices_worker.start()
        
    async def _load_voices(self) -> List[VoiceProfileResponse]:
        """Load voices asynchronously."""
        return await self.api_service.client.list_voice_profiles()
        
    def _on_voices_loaded(self, voices: List[VoiceProfileResponse]) -> None:
        """Handle loaded voices."""
        self.logger.info(f"Loaded {len(voices)} total voices from API")
        self.voices = [v for v in voices if v.is_cloned]  # Only show cloned voices
        self.logger.info(f"Found {len(self.voices)} cloned voices")
        
        self.voice_combo.clear()
        if not self.voices:
            self.voice_combo.addItem("No cloned voices available")
            self.voice_status_label.setText("Please clone a voice first")
        else:
            for voice in self.voices:
                self.voice_combo.addItem(voice.name, voice.id)
            self.voice_status_label.setText(f"{len(self.voices)} voices available")
            
        self.update_generate_button()
        self.is_loading_voices = False
        
    def _on_load_error(self, error_msg: str) -> None:
        """Handle voice loading error."""
        self.logger.error(f"Failed to load voices: {error_msg}")
        self.voice_status_label.setText("Failed to load voices")
        self.notification_manager.show_error("Failed to load voices")
        self.is_loading_voices = False
        
    def on_voice_selected(self, index: int) -> None:
        """Handle voice selection."""
        if index >= 0 and index < len(self.voices):
            self.selected_voice_id = self.voices[index].id
        else:
            self.selected_voice_id = None
        self.update_generate_button()
        
    def update_char_count(self) -> None:
        """Update character count label."""
        count = len(self.text_edit.toPlainText())
        
        # Calculate chunks and estimated time
        chunks = max(1, (count + 199) // 200)
        est_time = chunks * 90  # 90 seconds per chunk
        
        # Show warning for long texts with realistic time estimates
        if count > 1000:
            minutes = est_time // 60
            self.char_count_label.setText(f"Characters: {count:,} ⚠️ (~{minutes} minutes on CPU)")
            self.char_count_label.setStyleSheet("color: #ff6600;")
        elif count > 400:
            minutes = est_time // 60
            seconds = est_time % 60
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{est_time}s"
            self.char_count_label.setText(f"Characters: {count:,} ⚠️ (~{time_str} on CPU)")
            self.char_count_label.setStyleSheet("color: #ff9900;")
        elif count > 200:
            self.char_count_label.setText(f"Characters: {count:,} (2 chunks, ~3 min)")
            self.char_count_label.setStyleSheet("color: #0066cc;")
        else:
            self.char_count_label.setText(f"Characters: {count:,}")
            self.char_count_label.setStyleSheet("")
            
        self.update_generate_button()
        
    def update_generate_button(self) -> None:
        """Update generate button state."""
        text_available = bool(self.text_edit.toPlainText().strip())
        voice_selected = self.selected_voice_id is not None
        self.generate_button.setEnabled(text_available and voice_selected)
        
    def set_script_text(self, text: str) -> None:
        """Set the script text to generate audio from."""
        self.text_edit.setPlainText(text)
        self.script_text = text
        
    def set_suggested_filename(self, filename: str) -> None:
        """Set suggested filename for saving audio."""
        # Remove extension and sanitize
        import re
        self.suggested_filename = re.sub(r'[^\w\s-]', '', filename)
        self.suggested_filename = re.sub(r'[-\s]+', '-', self.suggested_filename)
        
    def test_with_sample(self) -> None:
        """Test TTS with a short sample text."""
        sample_text = "Hello! This is a test of the text to speech system. It should work quickly with this short text."
        self.text_edit.setPlainText(sample_text)
        # Automatically start generation if voice is selected
        if self.selected_voice_id:
            self.generate_audio()
        
    def generate_audio(self) -> None:
        """Generate audio from the script text."""
        if not self.selected_voice_id:
            QMessageBox.warning(self, "No Voice", "Please select a voice first.")
            return
            
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter some text to generate audio.")
            return
            
        self.logger.info(f"Starting audio generation with voice {self.selected_voice_id}, text length: {len(text)}")
        
        # Disable generate button during generation
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        # Hide result section if visible from previous generation
        self.result_group.setVisible(False)
        
        # Create progress dialog
        progress = ProgressDialog("Generating Audio", "Processing your text with the selected voice...", self)
        progress.set_indeterminate(True)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        # Add note about processing time with estimate
        estimated_chunks = max(1, (len(text) + 199) // 200)  # Round up division
        # Based on actual performance: ~90 seconds per chunk on CPU
        estimated_time = estimated_chunks * 90
        estimated_minutes = estimated_time // 60
        estimated_seconds = estimated_time % 60
        
        if len(text) > 200:  # Show estimate for any multi-chunk text
            time_str = f"{estimated_minutes}m {estimated_seconds}s" if estimated_minutes > 0 else f"{estimated_seconds} seconds"
            progress.message_label.setText(f"Processing your text with the selected voice...\n\n"
                                          f"⏱️ Estimated time: ~{time_str}\n"
                                          f"({estimated_chunks} chunks of text to process)\n\n"
                                          f"⚠️ Note: CPU processing is slow. GPU would be much faster.\n"
                                          f"The server may appear offline during processing.")
        
        # Clean up previous worker if exists
        if self.generate_worker and self.generate_worker.isRunning():
            self.generate_worker.quit()
            self.generate_worker.wait()
            
        # Show progress dialog
        self.logger.info("Showing progress dialog")
        progress.show()
        
        # Use AsyncWorker to generate audio
        self.generate_worker = AsyncWorker(self._generate_audio, text)
        self.generate_worker.result.connect(lambda data: self._on_audio_generated(data, progress))
        self.generate_worker.error.connect(lambda msg: self._on_generation_error(msg, progress))
        self.generate_worker.finished.connect(lambda: self._cleanup_worker('generate'))
        self.generate_worker.start()
        
    async def _generate_audio(self, text: str) -> bytes:
        """Generate audio asynchronously."""
        performance_monitor.increment("tts_generations")
        
        self.logger.info(f"Sending TTS request for {len(text)} characters")
        
        # Use synchronous requests for simplicity
        import requests
        
        url = f"{self.settings.api_url}/api/tts/generate/quick"
        
        try:
            # For very long texts, increase timeout significantly
            # Based on actual server logs, each chunk takes 70-90 seconds on CPU
            # With 200 char chunks, estimate number of chunks and add overhead
            estimated_chunks = max(1, (len(text) + 199) // 200)  # Round up division
            # Use 90 seconds per chunk + 60s for model loading
            timeout_seconds = estimated_chunks * 90 + 60
            self.logger.info(f"Using timeout of {timeout_seconds} seconds for {estimated_chunks} chunks")
            
            response = requests.post(
                url,
                data={
                    "text": text,
                    "voice_profile_id": str(self.selected_voice_id)
                },
                timeout=timeout_seconds
            )
            response.raise_for_status()
            
            # Get binary audio data
            audio_data = response.content
            
            self.logger.info(f"Received audio data: {len(audio_data)} bytes")
            
            return audio_data
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out after {timeout_seconds} seconds")
            raise Exception(f"Audio generation timed out. The text may be too long for quick generation. Try a shorter text or wait longer.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise Exception(f"Failed to generate audio: {str(e)}")
            
    def _on_audio_generated(self, audio_data: bytes, progress: ProgressDialog) -> None:
        """Handle successful audio generation."""
        progress.close()
        
        # Store the audio data
        self.generated_audio_data = audio_data
        
        # Show result section
        self.result_group.setVisible(True)
        text_len = len(self.text_edit.toPlainText())
        audio_size = len(audio_data) / 1024  # KB
        self.result_label.setText(f"✅ Audio generated successfully!\n"
                                 f"Text length: {text_len} characters\n"
                                 f"Audio size: {audio_size:.1f} KB")
        
        # Enable play/save buttons
        self.play_button.setEnabled(True)
        self.save_button.setEnabled(True)
        
        # Re-enable generate button
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Audio")
        
        # Show success notification
        self.notification_manager.show_success("Audio generated successfully!")
        
    def _on_generation_error(self, error_msg: str, progress: ProgressDialog) -> None:
        """Handle generation error."""
        progress.close()
        
        # Re-enable generate button
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Audio")
        
        if "cancelled" not in error_msg.lower():
            user_message = handle_error(Exception(error_msg), {"operation": "generate_audio"})
            self.notification_manager.show_error(user_message)
            QMessageBox.critical(self, "Generation Failed", user_message)
            
    def play_generated_audio(self) -> None:
        """Play the generated audio."""
        if not self.generated_audio_data:
            return
            
        try:
            from src.utils.audio import AudioPlayer
            
            # Create player if needed
            if not self.audio_player:
                self.audio_player = AudioPlayer()
                
            # Update button state
            if self.audio_player.is_playing:
                self.audio_player.stop()
                self.play_button.setText("▶ Play")
            else:
                self.play_button.setText("⏸ Stop")
                self.play_button.setEnabled(False)  # Disable during playback
                
                # Play audio
                if self.audio_player.play(self.generated_audio_data):
                    # Check playback status periodically
                    QTimer.singleShot(100, self._check_playback_status)
                else:
                    self.play_button.setText("▶ Play")
                    self.play_button.setEnabled(True)
                    QMessageBox.warning(self, "Playback Failed", "Failed to play audio")
                    
        except Exception as e:
            self.logger.error(f"Failed to play audio: {e}")
            QMessageBox.warning(self, "Playback Error", f"Failed to play audio: {str(e)}")
            
    def _check_playback_status(self) -> None:
        """Check if audio is still playing."""
        if self.audio_player and self.audio_player.is_playing:
            # Still playing, check again
            QTimer.singleShot(100, self._check_playback_status)
        else:
            # Playback finished
            self.play_button.setText("▶ Play")
            self.play_button.setEnabled(True)
            
    def save_generated_audio(self) -> None:
        """Save the generated audio to file."""
        if not self.generated_audio_data:
            return
            
        try:
            output_dir = Path(self.settings.data_dir) / "outputs"
            output_dir.mkdir(exist_ok=True)
            
            # Get save path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Audio File",
                str(output_dir / f"{self.suggested_filename}.wav"),
                "Audio Files (*.wav);;All Files (*.*)"
            )
            
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(self.generated_audio_data)
                    
                self.notification_manager.show_success(f"Audio saved to: {Path(file_path).name}")
                self.audio_generated.emit(file_path)
                
        except Exception as e:
            self.logger.error(f"Failed to save audio: {e}")
            user_message = handle_error(e, {"operation": "save_audio"})
            QMessageBox.critical(self, "Save Failed", user_message)
            
    def _cleanup_worker(self, worker_name: str) -> None:
        """Clean up finished worker."""
        if worker_name == 'load_voices' and self.load_voices_worker:
            self.load_voices_worker.deleteLater()
            self.load_voices_worker = None
        elif worker_name == 'generate' and self.generate_worker:
            self.generate_worker.deleteLater()
            self.generate_worker = None
            
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        # Disconnect API signals to prevent issues when dialog reopens
        try:
            self.api_service.connected.disconnect(self.on_api_connected)
        except:
            pass
            
        # Stop any playing audio
        if self.audio_player and self.audio_player.is_playing:
            self.audio_player.stop()
            
        # Clean up any running workers
        if self.load_voices_worker and self.load_voices_worker.isRunning():
            self.load_voices_worker.quit()
            self.load_voices_worker.wait()
            
        if self.generate_worker and self.generate_worker.isRunning():
            self.generate_worker.quit()
            self.generate_worker.wait()
            
        event.accept()