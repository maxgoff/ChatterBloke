#!/usr/bin/env python
"""Test script to verify Teleprompter functionality."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from src.gui.tabs.teleprompter import TeleprompterTab

def test_teleprompter():
    """Test the teleprompter tab in isolation."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Teleprompter Test")
    window.resize(1200, 800)
    
    # Create tab widget with just teleprompter
    tabs = QTabWidget()
    teleprompter_tab = TeleprompterTab()
    tabs.addTab(teleprompter_tab, "Teleprompter")
    
    window.setCentralWidget(tabs)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_teleprompter()