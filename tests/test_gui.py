"""Tests for GUI components."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.tabs.script_editor import ScriptEditorTab
from src.gui.tabs.settings import SettingsTab
from src.gui.tabs.teleprompter import TeleprompterTab
from src.gui.tabs.voice_manager import VoiceManagerTab
from src.gui.themes import ThemeManager, get_theme_manager
from src.gui.widgets.custom_widgets import StyledButton, ProgressDialog, FileSelector


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


class TestMainWindow:
    """Test MainWindow functionality."""
    
    def test_main_window_creation(self, qapp):
        """Test that main window can be created."""
        window = MainWindow()
        assert window is not None
        assert window.windowTitle().startswith("ChatterBloke")
        
    def test_tabs_created(self, qapp):
        """Test that all tabs are created."""
        window = MainWindow()
        assert window.tabs.count() == 4
        assert isinstance(window.voice_tab, VoiceManagerTab)
        assert isinstance(window.script_tab, ScriptEditorTab)
        assert isinstance(window.teleprompter_tab, TeleprompterTab)
        assert isinstance(window.settings_tab, SettingsTab)
        
    def test_menus_created(self, qapp):
        """Test that menus are created."""
        window = MainWindow()
        menubar = window.menuBar()
        assert menubar is not None
        
        # Check menu titles
        menus = [action.text() for action in menubar.actions()]
        assert "&File" in menus
        assert "&Edit" in menus
        assert "&View" in menus
        assert "&Help" in menus
        
    def test_status_bar_created(self, qapp):
        """Test that status bar is created."""
        window = MainWindow()
        assert window.status_bar is not None
        assert window.status_bar.currentMessage() == "Ready"


class TestTabs:
    """Test individual tab components."""
    
    def test_voice_manager_tab(self, qapp):
        """Test VoiceManagerTab creation."""
        tab = VoiceManagerTab()
        assert tab is not None
        assert tab.voice_list is not None
        assert tab.record_btn is not None
        
    def test_script_editor_tab(self, qapp):
        """Test ScriptEditorTab creation."""
        tab = ScriptEditorTab()
        assert tab is not None
        assert tab.text_editor is not None
        assert tab.script_list is not None
        
    def test_teleprompter_tab(self, qapp):
        """Test TeleprompterTab creation."""
        tab = TeleprompterTab()
        assert tab is not None
        assert tab.display_area is not None
        assert tab.play_btn is not None
        assert tab.speed_slider is not None
        
    def test_settings_tab(self, qapp):
        """Test SettingsTab creation."""
        tab = SettingsTab()
        assert tab is not None
        assert tab.save_btn is not None
        assert tab.reset_btn is not None


class TestThemeManager:
    """Test theme management."""
    
    def test_theme_manager_creation(self):
        """Test theme manager creation."""
        manager = ThemeManager()
        assert manager is not None
        assert len(manager.get_available_themes()) >= 2
        
    def test_theme_switching(self, qapp):
        """Test theme switching."""
        manager = get_theme_manager()
        
        # Test light theme
        manager.apply_theme("light", qapp)
        assert manager.current_theme == "light"
        
        # Test dark theme
        manager.apply_theme("dark", qapp)
        assert manager.current_theme == "dark"
        
    def test_toggle_theme(self, qapp):
        """Test theme toggling."""
        manager = get_theme_manager()
        manager.apply_theme("light", qapp)
        
        new_theme = manager.toggle_theme()
        assert new_theme == "dark"
        assert manager.current_theme == "dark"
        
        new_theme = manager.toggle_theme()
        assert new_theme == "light"
        assert manager.current_theme == "light"


class TestCustomWidgets:
    """Test custom widget components."""
    
    def test_styled_button(self, qapp):
        """Test StyledButton creation."""
        button = StyledButton("Test", "primary")
        assert button is not None
        assert button.text() == "Test"
        assert button.button_type == "primary"
        
        # Test type change
        button.set_type("danger")
        assert button.button_type == "danger"
        
    def test_progress_dialog(self, qapp):
        """Test ProgressDialog creation."""
        dialog = ProgressDialog("Test", "Testing...")
        assert dialog is not None
        assert dialog.windowTitle() == "Test"
        assert dialog.message_label.text() == "Testing..."
        
        # Test progress update
        dialog.set_progress(50)
        assert dialog.progress_bar.value() == 50
        
    def test_file_selector(self, qapp):
        """Test FileSelector creation."""
        selector = FileSelector("Test:", "*.txt")
        assert selector is not None
        assert selector.path_edit is not None
        assert selector.browse_button is not None
        
        # Test path setting
        selector.set_path("/test/path")
        assert selector.get_path() == "/test/path"