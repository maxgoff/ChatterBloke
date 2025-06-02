"""Main application window for ChatterBloke."""

import logging
from typing import Optional

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QToolButton,
)

from src.gui.services import get_api_service
from src.gui.tabs.script_editor import ScriptEditorTab
from src.gui.tabs.settings import SettingsTab
from src.gui.tabs.teleprompter import TeleprompterTab
from src.gui.tabs.voice_manager import VoiceManagerTab
from src.gui.themes import get_theme_manager
from src.gui.widgets.notification import NotificationManager
from src.utils.config import get_settings


class MainWindow(QMainWindow):
    """Main application window with tabs and menus."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.qt_settings = QSettings("ChatterBloke Team", "ChatterBloke")
        
        # Initialize API service
        self.api_service = get_api_service()
        self.api_service.connected.connect(self.on_api_connected)
        self.api_service.error.connect(self.on_api_error)
        
        # Initialize notification manager
        self.notification_manager = None  # Will be set after UI init
        
        self.init_ui()
        
        # Set up notification manager after UI is ready
        self.notification_manager = NotificationManager(self)
        self.restore_window_state()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.app_version}")
        self.setMinimumSize(800, 600)
        
        # Create central widget with tabs
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        
        # Create and add tabs
        self.voice_tab = VoiceManagerTab()
        self.script_tab = ScriptEditorTab()
        self.teleprompter_tab = TeleprompterTab()
        self.settings_tab = SettingsTab()
        
        self.tabs.addTab(self.voice_tab, "Voice Manager")
        self.tabs.addTab(self.script_tab, "Script Editor")
        self.tabs.addTab(self.teleprompter_tab, "Teleprompter")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Create menus
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
        # Connect signals
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def create_menus(self) -> None:
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Script", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new script")
        new_action.triggered.connect(self.new_script)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Script", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing script")
        open_action.triggered.connect(self.open_script)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Script", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current script")
        save_action.triggered.connect(self.save_script)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setStatusTip("Redo last action")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.setStatusTip("Cut selected text")
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setStatusTip("Copy selected text")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setStatusTip("Toggle fullscreen mode")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        theme_action = QAction("&Dark Theme", self)
        theme_action.setStatusTip("Toggle dark theme")
        theme_action.setCheckable(True)
        theme_action.setChecked(self.settings.theme == "dark")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About ChatterBloke")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction("&Documentation", self)
        help_action.setShortcut("F1")
        help_action.setStatusTip("Open documentation")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
    def create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_toolbar(self) -> None:
        """Create the main toolbar with quick access buttons."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # AI Assistant button
        ai_action = QAction("🤖 AI Assistant", self)
        ai_action.setToolTip("Open AI Assistant to generate or improve scripts")
        ai_action.triggered.connect(self.show_ai_assistant)
        toolbar.addAction(ai_action)
        
        toolbar.addSeparator()
        
        # Generate Audio button
        tts_action = QAction("🎙️ Generate Audio", self)
        tts_action.setToolTip("Generate audio from a script using a cloned voice")
        tts_action.triggered.connect(self.show_tts_dialog)
        toolbar.addAction(tts_action)
        
        toolbar.addSeparator()
        
        # Quick New Script
        new_script_action = QAction("📝 New Script", self)
        new_script_action.setToolTip("Create a new script (Ctrl+N)")
        new_script_action.triggered.connect(self.new_script)
        toolbar.addAction(new_script_action)
        
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change event."""
        tab_names = ["Voice Manager", "Script Editor", "Teleprompter", "Settings"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Switched to {tab_names[index]}")
            self.logger.info(f"Tab changed to: {tab_names[index]}")
            
    def new_script(self) -> None:
        """Create a new script."""
        # Switch to script editor tab
        self.tabs.setCurrentWidget(self.script_tab)
        self.script_tab.new_script()
        self.status_bar.showMessage("New script created")
        
    def open_script(self) -> None:
        """Open an existing script."""
        # Switch to script editor tab
        self.tabs.setCurrentWidget(self.script_tab)
        self.script_tab.open_script()
        
    def save_script(self) -> None:
        """Save the current script."""
        if self.tabs.currentWidget() == self.script_tab:
            self.script_tab.save_script()
            
    def undo(self) -> None:
        """Undo last action."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "undo"):
            current_tab.undo()
            
    def redo(self) -> None:
        """Redo last action."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "redo"):
            current_tab.redo()
            
    def cut(self) -> None:
        """Cut selected text."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "cut"):
            current_tab.cut()
            
    def copy(self) -> None:
        """Copy selected text."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "copy"):
            current_tab.copy()
            
    def paste(self) -> None:
        """Paste from clipboard."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "paste"):
            current_tab.paste()
            
    def toggle_fullscreen(self, checked: bool) -> None:
        """Toggle fullscreen mode."""
        if checked:
            self.showFullScreen()
            self.status_bar.showMessage("Fullscreen mode enabled")
        else:
            self.showNormal()
            self.status_bar.showMessage("Fullscreen mode disabled")
            
    def toggle_theme(self, checked: bool) -> None:
        """Toggle between light and dark theme."""
        theme_manager = get_theme_manager()
        theme = "dark" if checked else "light"
        theme_manager.apply_theme(theme)
        self.status_bar.showMessage(f"Switched to {theme} theme")
        self.logger.info(f"Theme changed to: {theme}")
        
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About ChatterBloke",
            f"<h2>{self.settings.app_name}</h2>"
            f"<p>Version {self.settings.app_version}</p>"
            "<p>A voice cloning and text-to-speech application.</p>"
            "<p>Built with Python, PyQt6, and Chatterbox-TTS.</p>",
        )
        
    def show_help(self) -> None:
        """Show help documentation."""
        # TODO: Implement help viewer
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation will be available in a future update.\n"
            "Please refer to README.md for now.",
        )
        
    def restore_window_state(self) -> None:
        """Restore window geometry and state from settings."""
        geometry = self.qt_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size and center on screen
            self.resize(self.settings.window_width, self.settings.window_height)
            self.center_on_screen()
            
        # Restore window state
        state = self.qt_settings.value("windowState")
        if state:
            self.restoreState(state)
            
    def save_window_state(self) -> None:
        """Save window geometry and state to settings."""
        self.qt_settings.setValue("geometry", self.saveGeometry())
        self.qt_settings.setValue("windowState", self.saveState())
        
    def center_on_screen(self) -> None:
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
            
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Save window state
        self.save_window_state()
        
        # Clean up tabs
        if hasattr(self.voice_tab, 'cleanup'):
            self.voice_tab.cleanup()
        
        # Stop API service
        self.logger.info("Stopping API service...")
        self.api_service.stop()
        
        # Give threads a moment to clean up
        QApplication.processEvents()
        
        # Confirm exit if there are unsaved changes
        # TODO: Check for unsaved changes in Phase 2
        
        self.logger.info("Application closing")
        event.accept()
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status change."""
        if is_connected:
            self.status_bar.showMessage("Connected to API server", 3000)
            if self.notification_manager:
                self.notification_manager.show_success("Connected to API server")
        else:
            self.status_bar.showMessage("API server not available - running in offline mode")
            if self.notification_manager:
                self.notification_manager.show_warning("API server not available - running in offline mode")
            
    def on_api_error(self, error_msg: str) -> None:
        """Handle API errors."""
        self.logger.error(f"API error: {error_msg}")
        self.status_bar.showMessage(f"API error: {error_msg}", 5000)
        if self.notification_manager:
            self.notification_manager.show_error(f"API error: {error_msg}")
            
    def show_ai_assistant(self) -> None:
        """Show AI Assistant dialog for script generation/improvement."""
        # Import here to avoid circular imports
        from src.gui.widgets.ai_assistant import AIAssistantWidget
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
        
        # Switch to script editor tab first
        self.tabs.setCurrentWidget(self.script_tab)
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Script Assistant")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create AI assistant widget
        assistant = AIAssistantWidget()
        
        # Set current script content if available
        if hasattr(self.script_tab, 'text_editor'):
            current_text = self.script_tab.text_editor.toPlainText()
            if current_text:
                assistant.set_current_script(current_text)
        
        # Connect signals if we're in the script editor
        if hasattr(self.script_tab, 'text_editor'):
            assistant.text_generated.connect(self.script_tab.text_editor.setPlainText)
            assistant.text_improved.connect(self.script_tab.text_editor.setPlainText)
            
        layout.addWidget(assistant)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def show_tts_dialog(self) -> None:
        """Show dialog to generate audio from a script."""
        # Import here to avoid circular imports
        from src.gui.widgets.tts_generation_dialog import TTSGenerationDialog
        
        # Create the dialog
        dialog = TTSGenerationDialog(self)
        
        # Pre-populate with current script if we're in the script editor
        if self.tabs.currentWidget() == self.script_tab and hasattr(self.script_tab, 'text_editor'):
            script_text = self.script_tab.text_editor.toPlainText().strip()
            if script_text:
                dialog.set_script_text(script_text)
                if hasattr(self.script_tab, 'script_title_label'):
                    title = self.script_tab.script_title_label.text()
                    if title and title != "Untitled Script":
                        dialog.set_suggested_filename(title)
        
        # Show the dialog
        dialog.exec()