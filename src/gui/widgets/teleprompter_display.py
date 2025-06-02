"""Teleprompter display widget with mirror mode support."""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QTransform, QTextOption
from PyQt6.QtWidgets import QTextEdit


class TeleprompterDisplay(QTextEdit):
    """Custom text display widget for teleprompter with mirror support."""
    
    def __init__(self):
        """Initialize the teleprompter display."""
        super().__init__()
        self.is_mirrored = False
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
    def set_mirrored(self, mirrored: bool) -> None:
        """Enable or disable mirror mode."""
        self.is_mirrored = mirrored
        self.update()  # Force repaint