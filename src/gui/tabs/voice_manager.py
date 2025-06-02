"""Voice Manager tab for managing voice profiles."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.gui.services import get_api_service
from src.utils.audio import AudioPlayer, AudioRecorder, get_audio_info, validate_audio_file
from src.utils.config import get_settings


class VoiceManagerTab(QWidget):
    """Tab for managing voice profiles and recordings."""

    def __init__(self) -> None:
        """Initialize the Voice Manager tab."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # API service
        self.api_service = get_api_service()
        self.api_service.connected.connect(self.on_api_connected)
        
        # Audio components
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        self.current_recording: Optional[bytes] = None
        self.current_recording_path: Optional[str] = None
        
        # Level meter update timer
        self.level_timer = QTimer()
        self.level_timer.timeout.connect(self._update_level_meter)
        
        # Voice profiles cache
        self.voice_profiles = {}
        
        # Test audio cache
        self.test_audio_path: Optional[str] = None
        
        # Track connection state to avoid redundant loads
        self.is_connected = False
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Voice profiles list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Voice details and recording
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (30% / 70%)
        splitter.setSizes([300, 700])
        
        # Initialize device list after all widgets are created
        self.refresh_devices()
        
    def create_left_panel(self) -> QWidget:
        """Create the left panel with voice profiles list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Voice Profiles")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Voice profiles list
        self.voice_list = QListWidget()
        self.voice_list.setAlternatingRowColors(True)
        self.voice_list.addItem("Loading...")
        self.voice_list.currentItemChanged.connect(self.on_voice_selected)
        layout.addWidget(self.voice_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_voice_btn = QPushButton("New")
        self.new_voice_btn.setToolTip("Create a new voice profile")
        self.new_voice_btn.clicked.connect(self.new_voice_profile)
        button_layout.addWidget(self.new_voice_btn)
        
        self.delete_voice_btn = QPushButton("Delete")
        self.delete_voice_btn.setToolTip("Delete selected voice profile")
        self.delete_voice_btn.clicked.connect(self.delete_voice_profile)
        self.delete_voice_btn.setEnabled(False)
        button_layout.addWidget(self.delete_voice_btn)
        
        self.import_voice_btn = QPushButton("Import")
        self.import_voice_btn.setToolTip("Import a voice profile")
        self.import_voice_btn.clicked.connect(self.import_voice_profile)
        button_layout.addWidget(self.import_voice_btn)
        
        layout.addLayout(button_layout)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with voice details and recording."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Recording section
        recording_group = QGroupBox("Voice Recording")
        recording_layout = QVBoxLayout(recording_group)
        
        # Device selection
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Input Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        device_layout.addWidget(self.device_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addStretch()
        
        recording_layout.addLayout(device_layout)
        
        # Recording status
        self.recording_status = QLabel("Ready to record")
        self.recording_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_status.setStyleSheet(
            "padding: 20px; background-color: #f0f0f0; border-radius: 5px;"
        )
        recording_layout.addWidget(self.recording_status)
        
        # Audio level meter
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        self.level_meter = QProgressBar()
        self.level_meter.setMaximum(100)
        self.level_meter.setTextVisible(False)
        self.level_meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        level_layout.addWidget(self.level_meter)
        recording_layout.addLayout(level_layout)
        
        # Recording controls
        controls_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setToolTip("Start recording audio from microphone")
        self.record_btn.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_btn)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setToolTip("Play recorded audio")
        self.play_btn.clicked.connect(self.play_recording)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        self.save_btn = QPushButton("Save Recording")
        self.save_btn.setToolTip("Save the current recording")
        self.save_btn.clicked.connect(self.save_recording)
        self.save_btn.setEnabled(False)
        controls_layout.addWidget(self.save_btn)
        
        recording_layout.addLayout(controls_layout)
        layout.addWidget(recording_group)
        
        # Voice details section
        details_group = QGroupBox("Voice Details")
        details_layout = QVBoxLayout(details_group)
        
        # Placeholder for voice details
        details_placeholder = QLabel("Select a voice profile to view details")
        details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_placeholder.setStyleSheet("color: #666; padding: 40px;")
        details_layout.addWidget(details_placeholder)
        
        layout.addWidget(details_group)
        
        # Voice cloning section
        cloning_group = QGroupBox("Voice Cloning")
        cloning_layout = QVBoxLayout(cloning_group)
        
        # Cloning status
        self.cloning_status = QLabel("Select a voice profile to enable cloning")
        self.cloning_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cloning_status.setStyleSheet("color: #666; padding: 10px;")
        cloning_layout.addWidget(self.cloning_status)
        
        # Cloning progress
        self.cloning_progress = QProgressBar()
        self.cloning_progress.setVisible(False)
        cloning_layout.addWidget(self.cloning_progress)
        
        # Test voice section
        test_layout = QVBoxLayout()
        test_header_layout = QHBoxLayout()
        test_header_layout.addWidget(QLabel("Test Voice:"))
        test_header_layout.addStretch()
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #666;")
        test_header_layout.addWidget(self.char_count_label)
        test_layout.addLayout(test_header_layout)
        
        self.test_text = QLineEdit()
        self.test_text.setPlaceholderText("Enter text to test the cloned voice...")
        self.test_text.setText("Hello, this is a test of my cloned voice.")
        self.test_text.textChanged.connect(self.update_char_count)
        test_layout.addWidget(self.test_text)
        
        # Update initial char count
        self.update_char_count()
        
        test_buttons_layout = QHBoxLayout()
        self.test_voice_btn = QPushButton("Test Voice")
        self.test_voice_btn.setToolTip("Generate test audio with cloned voice")
        self.test_voice_btn.clicked.connect(self.test_voice)
        self.test_voice_btn.setEnabled(False)
        test_buttons_layout.addWidget(self.test_voice_btn)
        
        self.play_test_btn = QPushButton("Play Test")
        self.play_test_btn.setToolTip("Play generated test audio")
        self.play_test_btn.clicked.connect(self.play_test_audio)
        self.play_test_btn.setEnabled(False)
        test_buttons_layout.addWidget(self.play_test_btn)
        
        test_layout.addLayout(test_buttons_layout)
        cloning_layout.addLayout(test_layout)
        
        # Clone button
        self.clone_btn = QPushButton("Start Voice Cloning")
        self.clone_btn.setToolTip("Start voice cloning process")
        self.clone_btn.clicked.connect(self.clone_voice)
        self.clone_btn.setEnabled(False)
        cloning_layout.addWidget(self.clone_btn)
        
        layout.addWidget(cloning_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
        
    def new_voice_profile(self) -> None:
        """Create a new voice profile."""
        self.logger.info("Creating new voice profile")
        # TODO: Implement in Phase 2
        self.recording_status.setText("New voice profile - Ready to record")
        
    def delete_voice_profile(self) -> None:
        """Delete the selected voice profile."""
        current_item = self.voice_list.currentItem()
        if not current_item or not current_item.data(Qt.ItemDataRole.UserRole):
            return
            
        voice_id = current_item.data(Qt.ItemDataRole.UserRole)
        voice_name = current_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the voice profile '{voice_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Show deleting status
            self.recording_status.setText(f"Deleting voice profile '{voice_name}'...")
            
            # Use the API service's event loop
            future = self.api_service.run_async(self._delete_voice_profile_async(voice_id))
            
            # Check result when ready
            def check_result():
                if future.done():
                    try:
                        success = future.result()
                        self.on_voice_profile_deleted(voice_id, voice_name, success)
                    except Exception as e:
                        self.logger.error(f"Failed to delete voice profile: {e}")
                        self.on_api_error(str(e))
                else:
                    # Check again in 50ms
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
        
    def import_voice_profile(self) -> None:
        """Import a voice profile from file."""
        self.logger.info("Importing voice profile")
        # TODO: Implement in Phase 2
        
    def refresh_devices(self) -> None:
        """Refresh the list of audio input devices."""
        self.device_combo.clear()
        devices = self.recorder.get_available_devices()
        
        if not devices:
            self.device_combo.addItem("No audio input devices found")
            if hasattr(self, 'record_btn'):
                self.record_btn.setEnabled(False)
            return
            
        for device in devices:
            device_text = device.name
            if device.is_default:
                device_text += " (Default)"
            self.device_combo.addItem(device_text, device.index)
            
        if hasattr(self, 'record_btn'):
            self.record_btn.setEnabled(True)
        
    def toggle_recording(self) -> None:
        """Toggle audio recording on/off."""
        if self.record_btn.text() == "Start Recording":
            # Get selected device
            device_index = self.device_combo.currentData()
            if device_index is not None:
                self.recorder.device = device_index
                
            # Set up level meter callback
            self.recorder.set_level_callback(self._update_level_callback)
            
            # Start recording
            if self.recorder.start_recording():
                self.logger.info("Started recording")
                self.record_btn.setText("Stop Recording")
                self.record_btn.setStyleSheet("background-color: #ff4444; color: white;")
                self.recording_status.setText("Recording... Speak into your microphone")
                self.play_btn.setEnabled(False)
                self.save_btn.setEnabled(False)
                self.level_timer.start(50)  # Update level meter every 50ms
            else:
                QMessageBox.warning(
                    self,
                    "Recording Error",
                    "Failed to start recording. Please check your audio device."
                )
        else:
            # Stop recording
            self.level_timer.stop()
            self.level_meter.setValue(0)
            
            audio_data = self.recorder.stop_recording()
            if audio_data:
                self.current_recording = audio_data
                self.logger.info("Stopped recording")
                self.record_btn.setText("Start Recording")
                self.record_btn.setStyleSheet("")
                self.recording_status.setText("Recording complete")
                self.play_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
            else:
                self.record_btn.setText("Start Recording")
                self.record_btn.setStyleSheet("")
                self.recording_status.setText("Recording failed")
                
    def play_recording(self) -> None:
        """Play the current recording."""
        if not self.current_recording:
            return
            
        self.logger.info("Playing recording")
        self.recording_status.setText("Playing recording...")
        
        if self.player.play(self.current_recording):
            # Update UI while playing
            self.play_btn.setEnabled(False)
            QTimer.singleShot(100, self._check_playback_status)
        else:
            self.recording_status.setText("Playback failed")
            
    def _check_playback_status(self) -> None:
        """Check if playback is still running."""
        if self.player.is_playing:
            QTimer.singleShot(100, self._check_playback_status)
        else:
            self.recording_status.setText("Playback complete")
            self.play_btn.setEnabled(True)
        
    def save_recording(self) -> None:
        """Save the current recording."""
        if not self.current_recording:
            return
            
        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Recording",
            str(self.settings.voices_samples_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"),
            "WAV Files (*.wav);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'wb') as f:
                    f.write(self.current_recording)
                self.logger.info(f"Saved recording to {filename}")
                self.recording_status.setText(f"Saved to {Path(filename).name}")
                
                # Ask if user wants to create a voice profile
                reply = QMessageBox.question(
                    self,
                    "Create Voice Profile",
                    "Would you like to create a voice profile from this recording?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.current_recording_path = filename
                    self.create_voice_profile_from_recording(filename)
                    
            except Exception as e:
                self.logger.error(f"Failed to save recording: {e}")
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save recording: {str(e)}"
                )
                
    def create_voice_profile_from_recording(self, audio_file: str) -> None:
        """Create a voice profile from a recording."""
        name, ok = QInputDialog.getText(
            self,
            "New Voice Profile",
            "Enter a name for this voice profile:"
        )
        
        if ok and name:
            # Show creating status
            self.recording_status.setText(f"Creating voice profile '{name}'...")
            
            # Use the API service's event loop
            future = self.api_service.run_async(self._create_voice_profile_async(name, audio_file))
            
            # Check result when ready
            def check_result():
                if future.done():
                    try:
                        result = future.result()
                        self.on_voice_profile_created(result)
                    except Exception as e:
                        self.logger.error(f"Failed to create voice profile: {e}")
                        self.on_api_error(str(e))
                else:
                    # Check again in 50ms
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
            
    def _update_level_callback(self, level: float) -> None:
        """Callback for audio level updates."""
        # Store level for timer to pick up
        self._current_level = int(level * 100)
        
    def _update_level_meter(self) -> None:
        """Update the level meter display."""
        if hasattr(self, '_current_level'):
            self.level_meter.setValue(self._current_level)
            # Change color based on level
            if self._current_level > 80:
                color = "#ff4444"  # Red for high levels
            elif self._current_level > 50:
                color = "#ffa500"  # Orange for medium levels
            else:
                color = "#4CAF50"  # Green for normal levels
                
            self.level_meter.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
        
    def clone_voice(self) -> None:
        """Start the voice cloning process."""
        current_item = self.voice_list.currentItem()
        if not current_item or not current_item.data(Qt.ItemDataRole.UserRole):
            return
            
        voice_id = current_item.data(Qt.ItemDataRole.UserRole)
        voice_profile = self.voice_profiles.get(voice_id)
        
        if not voice_profile:
            return
            
        self.logger.info(f"Starting voice cloning for profile: {voice_profile.name}")
        
        # Disable buttons during cloning
        self.clone_btn.setEnabled(False)
        self.test_voice_btn.setEnabled(False)
        
        # Show progress
        self.cloning_progress.setVisible(True)
        self.cloning_progress.setValue(0)
        self.cloning_status.setText(f"Cloning voice: {voice_profile.name}...")
        
        # Start cloning via API
        future = self.api_service.run_async(self._start_voice_cloning(voice_id))
        
        # Check result
        def check_clone_result():
            if future.done():
                try:
                    job_id = future.result()
                    if job_id:
                        # Start monitoring progress
                        self._monitor_cloning_progress(job_id, voice_id)
                    else:
                        self.cloning_status.setText("Failed to start voice cloning")
                        self.cloning_progress.setVisible(False)
                        self.clone_btn.setEnabled(True)
                except Exception as e:
                    self.logger.error(f"Voice cloning failed: {e}")
                    self.cloning_status.setText(f"Error: {str(e)}")
                    self.cloning_progress.setVisible(False)
                    self.clone_btn.setEnabled(True)
            else:
                QTimer.singleShot(50, check_clone_result)
                
        QTimer.singleShot(0, check_clone_result)
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status change."""
        if is_connected and not self.is_connected:
            # Load voice profiles when newly connected
            self.is_connected = True
            # Delay loading to ensure widget is fully initialized
            QTimer.singleShot(100, self.load_voice_profiles)
        elif not is_connected and self.is_connected:
            # Mark as disconnected
            self.is_connected = False
            self.voice_list.clear()
            self.voice_list.addItem("(Offline - API not available)")
            
    def on_voice_selected(self) -> None:
        """Handle voice profile selection."""
        current_item = self.voice_list.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole):
            voice_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.logger.info(f"Selected voice profile ID: {voice_id}")
            self.delete_voice_btn.setEnabled(True)
            
            # Enable clone button if voice has audio file
            voice_profile = self.voice_profiles.get(voice_id)
            if voice_profile and voice_profile.audio_file_path:
                self.clone_btn.setEnabled(True)
                if voice_profile.is_cloned:
                    self.cloning_status.setText(f"Voice '{voice_profile.name}' is ready for use")
                    self.test_voice_btn.setEnabled(True)
                else:
                    self.cloning_status.setText(f"Voice '{voice_profile.name}' can be cloned")
                    self.test_voice_btn.setEnabled(False)
            else:
                self.clone_btn.setEnabled(False)
                self.cloning_status.setText("Voice profile has no audio file")
                self.test_voice_btn.setEnabled(False)
        else:
            self.delete_voice_btn.setEnabled(False)
            self.clone_btn.setEnabled(False)
            self.test_voice_btn.setEnabled(False)
            self.cloning_status.setText("Select a voice profile to enable cloning")
            
    def load_voice_profiles(self) -> None:
        """Load voice profiles from API."""
        async def load_profiles():
            try:
                return await self.api_service.client.list_voice_profiles()
            except Exception as e:
                self.logger.error(f"Failed to load voice profiles: {e}")
                return None
                
        # Use the API service's event loop
        future = self.api_service.run_async(load_profiles())
        
        # Check result when ready
        def check_result():
            if future.done():
                try:
                    result = future.result()
                    self.on_voice_profiles_loaded(result)
                except Exception as e:
                    self.logger.error(f"Failed to load voice profiles: {e}")
                    self.on_api_error(str(e))
            else:
                # Check again in 50ms
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_voice_profiles_loaded(self, profiles) -> None:
        """Handle loaded voice profiles."""
        self.voice_list.clear()
        
        if not profiles:
            self.voice_list.addItem("(No voice profiles yet)")
            return
            
        # Cache profiles and populate list
        self.voice_profiles = {p.id: p for p in profiles}
        for profile in profiles:
            item = self.voice_list.addItem(profile.name)
            self.voice_list.item(self.voice_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, profile.id
            )
            
    def on_api_error(self, error_msg: str) -> None:
        """Handle API errors."""
        QMessageBox.warning(self, "API Error", f"Failed to communicate with server:\n{error_msg}")
        
    async def _create_voice_profile_async(self, name: str, audio_file_path: str) -> None:
        """Create voice profile via API (async)."""
        try:
            # First upload the audio file
            upload_result = await self.api_service.client.upload_audio_file(Path(audio_file_path))
            
            # Then create the voice profile
            profile = await self.api_service.client.create_voice_profile(
                name=name,
                audio_file_path=upload_result["file_path"],
                description=f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
            
            return profile
        except Exception as e:
            self.logger.error(f"Failed to create voice profile: {e}")
            raise
            
    async def _delete_voice_profile_async(self, voice_id: int) -> bool:
        """Delete voice profile via API (async)."""
        try:
            return await self.api_service.client.delete_voice_profile(voice_id)
        except Exception as e:
            self.logger.error(f"Failed to delete voice profile: {e}")
            raise
            
    def on_voice_profile_created(self, profile) -> None:
        """Handle successful voice profile creation."""
        if profile:
            self.logger.info(f"Voice profile created: {profile.name}")
            self.recording_status.setText(f"Voice profile '{profile.name}' created successfully")
            # Reload the voice profiles list
            self.load_voice_profiles()
        else:
            self.recording_status.setText("Failed to create voice profile")
            
    def on_voice_profile_deleted(self, voice_id: int, voice_name: str, success: bool) -> None:
        """Handle voice profile deletion result."""
        if success:
            self.logger.info(f"Voice profile '{voice_name}' deleted")
            self.recording_status.setText(f"Voice profile '{voice_name}' deleted successfully")
            # Reload the voice profiles list
            self.load_voice_profiles()
        else:
            self.recording_status.setText(f"Failed to delete voice profile '{voice_name}'")
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Failed to delete voice profile '{voice_name}'"
            )
            
    def cleanup(self) -> None:
        """Clean up resources when tab is closed."""
        # Stop any active audio operations
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        if self.player.is_playing:
            self.player.stop()
            
    async def _start_voice_cloning(self, voice_id: int) -> Optional[str]:
        """Start voice cloning via API."""
        try:
            response = await self.api_service.client._request(
                "POST",
                "/api/tts/clone",
                data={"voice_profile_id": voice_id}
            )
            return response.get("job_id")
        except Exception as e:
            self.logger.error(f"Failed to start voice cloning: {e}")
            raise
            
    def _monitor_cloning_progress(self, job_id: str, voice_id: int) -> None:
        """Monitor voice cloning progress."""
        async def check_status():
            try:
                response = await self.api_service.client._request(
                    "GET",
                    f"/api/tts/clone/status/{job_id}"
                )
                return response
            except Exception as e:
                self.logger.error(f"Failed to check cloning status: {e}")
                return None
                
        def update_progress():
            future = self.api_service.run_async(check_status())
            
            def handle_status():
                if future.done():
                    try:
                        status = future.result()
                        if status:
                            progress = status.get("progress", 0)
                            self.cloning_progress.setValue(progress)
                            
                            if status["status"] == "completed":
                                self.cloning_status.setText("Voice cloning completed!")
                                self.cloning_progress.setVisible(False)
                                self.clone_btn.setEnabled(True)
                                self.test_voice_btn.setEnabled(True)
                                
                                # Update voice profile
                                if voice_id in self.voice_profiles:
                                    self.voice_profiles[voice_id].is_cloned = True
                                    
                            elif status["status"] == "failed":
                                error = status.get("error", "Unknown error")
                                self.cloning_status.setText(f"Cloning failed: {error}")
                                self.cloning_progress.setVisible(False)
                                self.clone_btn.setEnabled(True)
                                
                            elif status["status"] == "processing":
                                # Continue monitoring
                                QTimer.singleShot(1000, update_progress)
                    except Exception as e:
                        self.logger.error(f"Error handling status: {e}")
                        self.cloning_status.setText("Error checking status")
                        self.cloning_progress.setVisible(False)
                        self.clone_btn.setEnabled(True)
                else:
                    QTimer.singleShot(50, handle_status)
                    
            QTimer.singleShot(0, handle_status)
            
        # Start monitoring
        update_progress()
        
    def test_voice(self) -> None:
        """Generate test audio with cloned voice."""
        current_item = self.voice_list.currentItem()
        if not current_item or not current_item.data(Qt.ItemDataRole.UserRole):
            return
            
        voice_id = current_item.data(Qt.ItemDataRole.UserRole)
        text = self.test_text.text().strip()
        
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to test")
            return
            
        self.logger.info(f"Generating test audio with voice {voice_id}")
        self.test_voice_btn.setEnabled(False)
        self.cloning_status.setText("Generating test audio...")
        
        # Generate via API
        async def generate_test():
            try:
                # Use the quick generation endpoint - returns binary audio
                # Must use form data, not JSON
                response = await self.api_service.client.client.post(
                    "/api/tts/generate/quick",
                    data={
                        "text": text,
                        "voice_profile_id": str(voice_id)  # Form data needs string
                    }
                )
                response.raise_for_status()
                # Get binary audio data
                audio_data = response.content
                # Save to temporary file
                temp_path = self.settings.temp_dir / f"test_voice_{voice_id}.wav"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                return str(temp_path)
            except Exception as e:
                self.logger.error(f"Failed to generate test audio: {e}")
                raise
                
        future = self.api_service.run_async(generate_test())
        
        def check_result():
            if future.done():
                try:
                    result = future.result()
                    # Save test audio path for playback
                    self.test_audio_path = result
                    self.cloning_status.setText("Test audio generated!")
                    self.test_voice_btn.setEnabled(True)
                    self.play_test_btn.setEnabled(True)
                except Exception as e:
                    self.logger.error(f"Test generation failed: {e}")
                    self.cloning_status.setText(f"Error: {str(e)}")
                    self.test_voice_btn.setEnabled(True)
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def play_test_audio(self) -> None:
        """Play the generated test audio."""
        if self.test_audio_path and Path(self.test_audio_path).exists():
            # Load and play the audio
            with open(self.test_audio_path, 'rb') as f:
                audio_data = f.read()
            if self.player.play(audio_data):
                self.cloning_status.setText("Playing test audio...")
                
    def update_char_count(self, text: Optional[str] = None) -> None:
        """Update character count label."""
        if text is None:
            text = self.test_text.text()
        count = len(text)
        self.char_count_label.setText(f"{count} characters")
        self.char_count_label.setStyleSheet("color: #666;")  # Always normal color
            
    def _check_test_playback_status(self) -> None:
        """Check if test playback is still running."""
        if self.player.is_playing:
            QTimer.singleShot(100, self._check_test_playback_status)
        else:
            self.cloning_status.setText("Test playback complete")
            self.play_test_btn.setEnabled(True)