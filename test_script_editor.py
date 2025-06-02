#!/usr/bin/env python
"""Test script to verify Script Editor functionality."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from src.gui.tabs.script_editor import ScriptEditorTab

def test_script_editor():
    """Test the script editor tab in isolation."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Script Editor Test")
    window.resize(1200, 800)
    
    # Create tab widget with just script editor
    tabs = QTabWidget()
    script_tab = ScriptEditorTab()
    tabs.addTab(script_tab, "Script Editor")
    
    window.setCentralWidget(tabs)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_script_editor()