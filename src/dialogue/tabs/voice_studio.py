"""Voice studio tab for managing voices in dialogue application."""

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.gui.services import APIService
from src.gui.tabs.voice_manager import VoiceManagerTab


class VoiceStudioTab(QWidget):
    """Simplified voice management for dialogue application."""
    
    def __init__(self, api_service: APIService):
        super().__init__()
        self.api_service = api_service
        self.logger = logging.getLogger(__name__)
        
        # We'll embed the existing voice manager functionality
        self.voice_manager = VoiceManagerTab()
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Add header
        header = QLabel("Voice Studio - Record and Clone Voices for Your Dialogues")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Add the voice manager
        layout.addWidget(self.voice_manager, 1)
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.voice_manager.cleanup()