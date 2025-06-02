#!/usr/bin/env python
"""Test script to verify mirror mode functionality."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QCheckBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from src.gui.widgets.teleprompter_display import TeleprompterDisplay


def test_mirror_mode():
    """Test the mirror mode functionality."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Mirror Mode Test")
    window.resize(800, 600)
    
    # Central widget
    central = QWidget()
    window.setCentralWidget(central)
    
    # Layout
    layout = QVBoxLayout(central)
    
    # Mirror mode checkbox
    mirror_check = QCheckBox("Mirror Mode")
    layout.addWidget(mirror_check)
    
    # Teleprompter display
    display = TeleprompterDisplay()
    display.setFont(QFont("Arial", 24))
    display.setStyleSheet("""
        QTextEdit {
            background-color: black;
            color: white;
            padding: 20px;
        }
    """)
    display.setPlainText("""This is a test of the mirror mode.
    
When mirror mode is enabled, this text should appear flipped horizontally.

This is useful for teleprompter glass setups where the text is reflected.

MIRROR TEST 123

The quick brown fox jumps over the lazy dog.""")
    
    # Connect mirror checkbox
    mirror_check.toggled.connect(display.set_mirrored)
    
    layout.addWidget(display)
    
    # Test button to verify interaction
    test_btn = QPushButton("Test Button")
    test_btn.clicked.connect(lambda: print("Button clicked - mirror mode:", display.is_mirrored))
    layout.addWidget(test_btn)
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_mirror_mode()