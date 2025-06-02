"""Settings tab for application configuration."""

import logging
from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import get_settings, reset_settings


class SettingsTab(QWidget):
    """Tab for application settings and configuration."""

    def __init__(self) -> None:
        """Initialize the Settings tab."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Add settings groups
        scroll_layout.addWidget(self.create_general_settings())
        scroll_layout.addWidget(self.create_audio_settings())
        scroll_layout.addWidget(self.create_ui_settings())
        scroll_layout.addWidget(self.create_api_settings())
        scroll_layout.addWidget(self.create_backup_settings())
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Buttons at the bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
    def create_general_settings(self) -> QGroupBox:
        """Create general settings group."""
        group = QGroupBox("General Settings")
        layout = QFormLayout(group)
        
        # Application name (read-only)
        self.app_name_edit = QLineEdit()
        self.app_name_edit.setReadOnly(True)
        layout.addRow("Application Name:", self.app_name_edit)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("Log Level:", self.log_level_combo)
        
        # Debug mode
        self.debug_check = QCheckBox("Enable Debug Mode")
        layout.addRow("Debug:", self.debug_check)
        
        return group
        
    def create_audio_settings(self) -> QGroupBox:
        """Create audio settings group."""
        group = QGroupBox("Audio Settings")
        layout = QFormLayout(group)
        
        # Sample rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["22050", "44100", "48000"])
        self.sample_rate_combo.setEditable(True)
        layout.addRow("Sample Rate (Hz):", self.sample_rate_combo)
        
        # Channels
        self.channels_spin = QSpinBox()
        self.channels_spin.setMinimum(1)
        self.channels_spin.setMaximum(2)
        layout.addRow("Audio Channels:", self.channels_spin)
        
        # Max recording duration
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setMinimum(10)
        self.max_duration_spin.setMaximum(3600)
        self.max_duration_spin.setSuffix(" seconds")
        layout.addRow("Max Recording Duration:", self.max_duration_spin)
        
        # Audio chunk size
        self.chunk_size_combo = QComboBox()
        self.chunk_size_combo.addItems(["512", "1024", "2048", "4096"])
        layout.addRow("Audio Chunk Size:", self.chunk_size_combo)
        
        return group
        
    def create_ui_settings(self) -> QGroupBox:
        """Create UI settings group."""
        group = QGroupBox("User Interface")
        layout = QFormLayout(group)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        layout.addRow("Theme:", self.theme_combo)
        
        # Font family
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Arial", "Helvetica", "Times New Roman", "Courier New"])
        self.font_family_combo.setEditable(True)
        layout.addRow("Font Family:", self.font_family_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setSuffix(" pt")
        layout.addRow("Font Size:", self.font_size_spin)
        
        # Window dimensions
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setMinimum(800)
        self.window_width_spin.setMaximum(3840)
        self.window_width_spin.setSuffix(" px")
        layout.addRow("Default Window Width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setMinimum(600)
        self.window_height_spin.setMaximum(2160)
        self.window_height_spin.setSuffix(" px")
        layout.addRow("Default Window Height:", self.window_height_spin)
        
        return group
        
    def create_api_settings(self) -> QGroupBox:
        """Create API settings group."""
        group = QGroupBox("API Settings")
        layout = QFormLayout(group)
        
        # API host
        self.api_host_edit = QLineEdit()
        layout.addRow("API Host:", self.api_host_edit)
        
        # API port
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setMinimum(1024)
        self.api_port_spin.setMaximum(65535)
        layout.addRow("API Port:", self.api_port_spin)
        
        # Ollama host
        self.ollama_host_edit = QLineEdit()
        layout.addRow("Ollama Host:", self.ollama_host_edit)
        
        # Ollama model
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.addItems(["llama2", "mistral", "codellama"])
        self.ollama_model_combo.setEditable(True)
        layout.addRow("Ollama Model:", self.ollama_model_combo)
        
        # Ollama timeout
        self.ollama_timeout_spin = QSpinBox()
        self.ollama_timeout_spin.setMinimum(5)
        self.ollama_timeout_spin.setMaximum(300)
        self.ollama_timeout_spin.setSuffix(" seconds")
        layout.addRow("Ollama Timeout:", self.ollama_timeout_spin)
        
        return group
        
    def create_backup_settings(self) -> QGroupBox:
        """Create backup settings group."""
        group = QGroupBox("Backup Settings")
        layout = QFormLayout(group)
        
        # Backup enabled
        self.backup_enabled_check = QCheckBox("Enable Automatic Backups")
        layout.addRow("Backups:", self.backup_enabled_check)
        
        # Backup interval
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setMinimum(3600)  # 1 hour
        self.backup_interval_spin.setMaximum(604800)  # 1 week
        self.backup_interval_spin.setSingleStep(3600)
        self.backup_interval_spin.setSuffix(" seconds")
        layout.addRow("Backup Interval:", self.backup_interval_spin)
        
        # Retention days
        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setMinimum(1)
        self.retention_days_spin.setMaximum(365)
        self.retention_days_spin.setSuffix(" days")
        layout.addRow("Retention Period:", self.retention_days_spin)
        
        return group
        
    def load_settings(self) -> None:
        """Load current settings into the UI."""
        # General settings
        self.app_name_edit.setText(self.settings.app_name)
        self.log_level_combo.setCurrentText(self.settings.log_level)
        self.debug_check.setChecked(self.settings.debug)
        
        # Audio settings
        self.sample_rate_combo.setCurrentText(str(self.settings.audio_sample_rate))
        self.channels_spin.setValue(self.settings.audio_channels)
        self.max_duration_spin.setValue(self.settings.max_recording_duration)
        self.chunk_size_combo.setCurrentText(str(self.settings.audio_chunk_size))
        
        # UI settings
        self.theme_combo.setCurrentText(self.settings.theme)
        self.font_family_combo.setCurrentText(self.settings.font_family)
        self.font_size_spin.setValue(self.settings.font_size)
        self.window_width_spin.setValue(self.settings.window_width)
        self.window_height_spin.setValue(self.settings.window_height)
        
        # API settings
        self.api_host_edit.setText(self.settings.api_host)
        self.api_port_spin.setValue(self.settings.api_port)
        self.ollama_host_edit.setText(self.settings.ollama_host)
        self.ollama_model_combo.setCurrentText(self.settings.ollama_model)
        self.ollama_timeout_spin.setValue(self.settings.ollama_timeout)
        
        # Backup settings
        self.backup_enabled_check.setChecked(self.settings.backup_enabled)
        self.backup_interval_spin.setValue(self.settings.backup_interval)
        self.retention_days_spin.setValue(self.settings.backup_retention_days)
        
    def get_settings_dict(self) -> Dict[str, Any]:
        """Get current settings from UI as dictionary."""
        return {
            # General
            "log_level": self.log_level_combo.currentText(),
            "debug": self.debug_check.isChecked(),
            
            # Audio
            "audio_sample_rate": int(self.sample_rate_combo.currentText()),
            "audio_channels": self.channels_spin.value(),
            "max_recording_duration": self.max_duration_spin.value(),
            "audio_chunk_size": int(self.chunk_size_combo.currentText()),
            
            # UI
            "theme": self.theme_combo.currentText(),
            "font_family": self.font_family_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "window_width": self.window_width_spin.value(),
            "window_height": self.window_height_spin.value(),
            
            # API
            "api_host": self.api_host_edit.text(),
            "api_port": self.api_port_spin.value(),
            "ollama_host": self.ollama_host_edit.text(),
            "ollama_model": self.ollama_model_combo.currentText(),
            "ollama_timeout": self.ollama_timeout_spin.value(),
            
            # Backup
            "backup_enabled": self.backup_enabled_check.isChecked(),
            "backup_interval": self.backup_interval_spin.value(),
            "backup_retention_days": self.retention_days_spin.value(),
        }
        
    def save_settings(self) -> None:
        """Save settings to configuration."""
        try:
            # TODO: Implement actual settings saving in Phase 1
            settings_dict = self.get_settings_dict()
            self.logger.info(f"Saving settings: {settings_dict}")
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully.\n"
                "Some changes may require restarting the application."
            )
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {str(e)}"
            )
            
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            reset_settings()
            self.settings = get_settings()
            self.load_settings()
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to defaults."
            )
            
    def cancel_changes(self) -> None:
        """Cancel changes and reload settings."""
        self.load_settings()
        QMessageBox.information(
            self,
            "Changes Cancelled",
            "All changes have been discarded."
        )