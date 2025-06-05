"""Project manager tab for saving and loading dialogue projects."""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.gui.services import APIService


class ProjectManagerTab(QWidget):
    """Tab for managing dialogue projects."""
    
    def __init__(self, api_service: APIService):
        super().__init__()
        self.api_service = api_service
        self.logger = logging.getLogger(__name__)
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Placeholder
        label = QLabel("Project Manager - Coming Soon")
        label.setStyleSheet("font-size: 24px; color: gray;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        info = QLabel(
            "This tab will allow you to:\n"
            "• Save dialogue projects\n"
            "• Load existing projects\n"
            "• Export complete projects\n"
            "• Manage project files\n"
            "• Import/export dialogue scripts"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
    def save_current_project(self) -> None:
        """Save the current project."""
        self.logger.info("Saving project...")
        
    def open_project(self) -> None:
        """Open an existing project."""
        self.logger.info("Opening project...")
        
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
        
        
from PyQt6.QtCore import Qt