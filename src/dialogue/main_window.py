"""Main window for ChatterBloke Dialogue application."""

import logging
from typing import Optional

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QWidget,
)

from src.gui.services import get_api_service
from src.dialogue.tabs.voice_studio import VoiceStudioTab
from src.dialogue.tabs.dialogue_editor import DialogueEditorTab
from src.dialogue.tabs.audio_generator import AudioGeneratorTab
from src.dialogue.tabs.project_manager import ProjectManagerTab
from src.gui.themes import get_theme_manager
from src.utils.config import get_settings


class DialogueMainWindow(QMainWindow):
    """Main window for dialogue generation application."""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.api_service = get_api_service()
        
        # Initialize UI
        self.setWindowTitle("ChatterBloke Dialogue - Two-Voice Conversation Generator")
        self.setMinimumSize(1200, 800)
        
        # Create UI elements
        self.create_central_widget()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        
        # Connect signals
        self.api_service.connected.connect(self.on_api_connected)
        self.api_service.error.connect(self.on_api_error)
        
        # Restore window state
        self.restore_window_state()
        
        # Start API service
        self.api_service.start()
        
    def create_central_widget(self) -> None:
        """Create the central widget with tabs."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tabs
        self.voice_studio_tab = VoiceStudioTab(self.api_service)
        self.dialogue_editor_tab = DialogueEditorTab(self.api_service)
        self.audio_generator_tab = AudioGeneratorTab(self.api_service)
        self.project_manager_tab = ProjectManagerTab(self.api_service)
        
        # Add tabs
        self.tabs.addTab(self.voice_studio_tab, "🎙️ Voice Studio")
        self.tabs.addTab(self.dialogue_editor_tab, "✍️ Dialogue Editor")
        self.tabs.addTab(self.audio_generator_tab, "🎵 Audio Generator")
        self.tabs.addTab(self.project_manager_tab, "📁 Projects")
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_dialogue_action = QAction("&New Dialogue", self)
        new_dialogue_action.setShortcut("Ctrl+N")
        new_dialogue_action.triggered.connect(self.new_dialogue)
        file_menu.addAction(new_dialogue_action)
        
        open_project_action = QAction("&Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        save_project_action = QAction("&Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        export_audio_action = QAction("Export &Audio", self)
        export_audio_action.triggered.connect(self.export_audio)
        file_menu.addAction(export_audio_action)
        
        export_script_action = QAction("Export &Script", self)
        export_script_action.triggered.connect(self.export_script)
        file_menu.addAction(export_script_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.dialogue_editor_tab.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.dialogue_editor_tab.redo)
        edit_menu.addAction(redo_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        ai_assist_action = QAction("&AI Dialogue Assistant", self)
        ai_assist_action.setShortcut("Ctrl+G")
        ai_assist_action.triggered.connect(self.show_ai_assistant)
        tools_menu.addAction(ai_assist_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # New Dialogue
        new_action = QAction("📝 New Dialogue", self)
        new_action.setToolTip("Create a new dialogue project")
        new_action.triggered.connect(self.new_dialogue)
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # AI Assistant
        ai_action = QAction("🤖 AI Assistant", self)
        ai_action.setToolTip("Generate dialogue with AI")
        ai_action.triggered.connect(self.show_ai_assistant)
        toolbar.addAction(ai_action)
        
        toolbar.addSeparator()
        
        # Generate Audio
        generate_action = QAction("🎵 Generate Audio", self)
        generate_action.setToolTip("Generate audio from current dialogue")
        generate_action.triggered.connect(self.generate_audio)
        toolbar.addAction(generate_action)
        
        toolbar.addSeparator()
        
        # Preview
        preview_action = QAction("▶️ Preview", self)
        preview_action.setToolTip("Preview generated audio")
        preview_action.triggered.connect(self.preview_audio)
        toolbar.addAction(preview_action)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        # Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.setToolTip("Exit application")
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)
        
    def create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        tab_names = ["Voice Studio", "Dialogue Editor", "Audio Generator", "Projects"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Switched to {tab_names[index]}")
            self.logger.info(f"Tab changed to: {tab_names[index]}")
            
            # If switching to Audio Generator, refresh voice profiles and set dialogue
            if index == 2:  # Audio Generator tab
                # Load voices first
                self.audio_generator_tab.load_voice_profiles()
                
                # Then set the current dialogue from the editor
                dialogue = self.dialogue_editor_tab.get_dialogue()
                if dialogue:
                    self.audio_generator_tab.set_dialogue(dialogue)
            
    def new_dialogue(self) -> None:
        """Create a new dialogue project."""
        self.dialogue_editor_tab.new_dialogue()
        self.tabs.setCurrentWidget(self.dialogue_editor_tab)
        
    def open_project(self) -> None:
        """Open an existing project."""
        self.project_manager_tab.open_project()
        self.tabs.setCurrentWidget(self.project_manager_tab)
        
    def save_project(self) -> None:
        """Save current project."""
        self.project_manager_tab.save_current_project()
        
    def export_audio(self) -> None:
        """Export generated audio."""
        self.audio_generator_tab.export_audio()
        
    def export_script(self) -> None:
        """Export dialogue script."""
        self.dialogue_editor_tab.export_script()
        
    def show_ai_assistant(self) -> None:
        """Show AI dialogue assistant."""
        self.tabs.setCurrentWidget(self.dialogue_editor_tab)
        self.dialogue_editor_tab.show_ai_assistant()
        
    def generate_audio(self) -> None:
        """Generate audio from current dialogue."""
        # Get current dialogue
        dialogue = self.dialogue_editor_tab.get_dialogue()
        if dialogue:
            self.audio_generator_tab.set_dialogue(dialogue)
            self.tabs.setCurrentWidget(self.audio_generator_tab)
            self.audio_generator_tab.generate()
        else:
            QMessageBox.warning(self, "No Dialogue", "Please create or load a dialogue first.")
            
    def preview_audio(self) -> None:
        """Preview generated audio."""
        self.tabs.setCurrentWidget(self.audio_generator_tab)
        self.audio_generator_tab.preview()
        
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About ChatterBloke Dialogue",
            "ChatterBloke Dialogue v0.1.0\n\n"
            "A two-voice conversation generator using AI and voice cloning.\n\n"
            "Part of the ChatterBloke suite of audio tools."
        )
        
    def save_window_state(self) -> None:
        """Save window geometry and state."""
        settings = QSettings()
        settings.setValue("dialogue/geometry", self.saveGeometry())
        settings.setValue("dialogue/windowState", self.saveState())
        
    def restore_window_state(self) -> None:
        """Restore window geometry and state."""
        settings = QSettings()
        geometry = settings.value("dialogue/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("dialogue/windowState")
        if state:
            self.restoreState(state)
            
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Check for unsaved changes
        if self.dialogue_editor_tab.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
                if self.dialogue_editor_tab.has_unsaved_changes():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
                
        # Save window state
        self.save_window_state()
        
        # Clean up tabs
        self.logger.info("Cleaning up tabs...")
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'cleanup'):
                tab.cleanup()
                
        # Stop API service
        self.logger.info("Stopping API service...")
        self.api_service.stop()
        
        # Clean up timers
        for widget in self.findChildren(QTimer):
            widget.stop()
            
        QApplication.processEvents()
        
        self.logger.info("ChatterBloke Dialogue closing")
        event.accept()
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status."""
        if is_connected:
            self.status_bar.showMessage("Connected to API server", 3000)
        else:
            self.status_bar.showMessage("API server not available")
            
    def on_api_error(self, error_msg: str) -> None:
        """Handle API errors."""
        self.logger.error(f"API error: {error_msg}")
        self.status_bar.showMessage(f"API error: {error_msg}", 5000)