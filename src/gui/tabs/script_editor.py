"""Script Editor tab for creating and editing scripts."""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QSpinBox,
    QSlider,
    QFormLayout,
    QMenu,
)

from src.gui.services import get_api_service
from src.gui.widgets.ai_assistant import AIAssistantWidget


class ScriptEditorTab(QWidget):
    """Tab for editing scripts with AI assistance."""

    def __init__(self) -> None:
        """Initialize the Script Editor tab."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_script_id: Optional[int] = None
        self.scripts_cache: Dict[int, Dict] = {}
        self.has_unsaved_changes = False
        
        # API service
        self.api_service = get_api_service()
        self.api_service.connected.connect(self.on_api_connected)
        self.is_connected = False
        
        self.init_ui()
        
        # Check if already connected and load scripts
        if self.api_service.client:
            self.is_connected = True
            QTimer.singleShot(100, self.load_scripts)
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status change."""
        if is_connected and not self.is_connected:
            self.is_connected = True
            # Load scripts when newly connected
            QTimer.singleShot(100, self.load_scripts)
        elif not is_connected and self.is_connected:
            self.is_connected = False
            self.script_list.clear()
            self.script_list.addItem("(Offline - API not available)")
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Script list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Script editor
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (25% / 75%)
        splitter.setSizes([250, 750])
        
    def create_toolbar(self) -> QToolBar:
        """Create the editor toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # New script action
        new_action = toolbar.addAction("New")
        new_action.setToolTip("Create a new script (Ctrl+N)")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_script)
        
        # Open script action
        open_action = toolbar.addAction("Open")
        open_action.setToolTip("Open a script file (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_script)
        
        # Save script action
        save_action = toolbar.addAction("Save")
        save_action.setToolTip("Save the current script (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_script)
        
        # Export script action
        export_action = toolbar.addAction("Export")
        export_action.setToolTip("Export script to file")
        export_action.triggered.connect(self.export_script)
        
        toolbar.addSeparator()
        
        # Text formatting actions
        bold_action = toolbar.addAction("Bold")
        bold_action.setToolTip("Make selected text bold")
        bold_action.triggered.connect(self.make_bold)
        
        italic_action = toolbar.addAction("Italic")
        italic_action.setToolTip("Make selected text italic")
        italic_action.triggered.connect(self.make_italic)
        
        toolbar.addSeparator()
        
        # AI assistance action
        ai_action = toolbar.addAction("AI Assist")
        ai_action.setToolTip("Get AI assistance for your script")
        ai_action.triggered.connect(self.show_ai_assist)
        
        # Generate speech action
        tts_action = toolbar.addAction("Generate Speech")
        tts_action.setToolTip("Generate speech from the script")
        tts_action.triggered.connect(self.generate_speech)
        
        return toolbar
        
    def create_left_panel(self) -> QWidget:
        """Create the left panel with script list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Scripts")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.addItem("(No scripts yet)")
        self.script_list.currentItemChanged.connect(self.on_script_selected)
        self.script_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self.show_script_context_menu)
        layout.addWidget(self.script_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_script_btn = QPushButton("New")
        self.new_script_btn.setToolTip("Create a new script")
        self.new_script_btn.clicked.connect(self.new_script)
        button_layout.addWidget(self.new_script_btn)
        
        self.delete_script_btn = QPushButton("Delete")
        self.delete_script_btn.setToolTip("Delete selected script")
        self.delete_script_btn.clicked.connect(self.delete_script)
        self.delete_script_btn.setEnabled(False)
        button_layout.addWidget(self.delete_script_btn)
        
        layout.addLayout(button_layout)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with text editor."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Script title/info bar
        info_layout = QHBoxLayout()
        self.script_title_label = QLabel("New Script")
        self.script_title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.script_title_label)
        
        info_layout.addStretch()
        
        self.word_count_label = QLabel("Words: 0")
        info_layout.addWidget(self.word_count_label)
        
        layout.addLayout(info_layout)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Arial", 12))
        self.text_editor.setPlaceholderText(
            "Start typing your script here...\n\n"
            "Tips:\n"
            "- Use the AI Assist button for help with your script\n"
            "- Save your work regularly\n"
            "- You can generate speech from your script when ready"
        )
        self.text_editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_editor)
        
        # Status bar
        self.editor_status = QLabel("Ready")
        self.editor_status.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px;"
        )
        layout.addWidget(self.editor_status)
        
        return panel
        
    def new_script(self) -> None:
        """Create a new script."""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new script?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_script()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        # Get title for new script
        title, ok = QInputDialog.getText(
            self, 
            "New Script", 
            "Enter script title:",
            text=f"Script {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        if ok and title:
            self.logger.info(f"Creating new script: {title}")
            
            # Create via API
            async def create_script():
                try:
                    return await self.api_service.client.create_script(
                        title=title,
                        content=""
                    )
                except Exception as e:
                    self.logger.error(f"Failed to create script: {e}")
                    raise
                    
            future = self.api_service.run_async(create_script())
            
            def check_result():
                if future.done():
                    try:
                        script = future.result()
                        self.on_script_created(script)
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to create script: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
        
    def open_script(self) -> None:
        """Open a script from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Script",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            self.logger.info(f"Opening script: {filename}")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ask user if they want to import to database
                reply = QMessageBox.question(
                    self,
                    "Import Script",
                    "Do you want to import this script to the database?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Import to database
                    title = filename.split('/')[-1].rsplit('.', 1)[0]  # Remove extension
                    
                    async def import_script():
                        try:
                            return await self.api_service.client.create_script(
                                title=title,
                                content=content
                            )
                        except Exception as e:
                            self.logger.error(f"Failed to import script: {e}")
                            raise
                            
                    future = self.api_service.run_async(import_script())
                    
                    def check_result():
                        if future.done():
                            try:
                                script = future.result()
                                self.on_script_created(script)
                                self.text_editor.setPlainText(content)
                                self.editor_status.setText(f"Imported: {filename}")
                            except Exception as e:
                                self.editor_status.setText(f"Error: {str(e)}")
                                QMessageBox.critical(self, "Error", f"Failed to import script: {str(e)}")
                        else:
                            QTimer.singleShot(50, check_result)
                            
                    QTimer.singleShot(0, check_result)
                else:
                    # Just load content without saving to database
                    self.text_editor.setPlainText(content)
                    self.script_title_label.setText(filename.split('/')[-1])
                    self.editor_status.setText(f"Opened: {filename}")
                    self.current_script_id = None  # Not saved in database
                    
            except Exception as e:
                self.logger.error(f"Error opening file: {e}")
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
                
    def export_script(self) -> None:
        """Export the current script to a file."""
        content = self.text_editor.toPlainText().strip()
        if not content:
            self.editor_status.setText("Nothing to export")
            return
            
        # Get suggested filename from script title
        title = self.script_title_label.text()
        if title == "New Script":
            title = "script"
        # Clean filename
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Script",
            f"{clean_title}.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.editor_status.setText(f"Exported: {filename}")
                self.logger.info(f"Exported script to: {filename}")
            except Exception as e:
                self.logger.error(f"Error exporting file: {e}")
                QMessageBox.critical(self, "Error", f"Could not export file: {str(e)}")
                
    def save_script(self) -> None:
        """Save the current script."""
        if not self.text_editor.toPlainText().strip():
            self.editor_status.setText("Nothing to save")
            return
            
        if self.current_script_id:
            # Update existing script
            self.logger.info(f"Saving script ID: {self.current_script_id}")
            content = self.text_editor.toPlainText()
            
            async def update_script():
                try:
                    # Get current title from the label
                    title = self.script_title_label.text()
                    return await self.api_service.client.update_script(
                        script_id=self.current_script_id,
                        title=title,
                        content=content
                    )
                except Exception as e:
                    self.logger.error(f"Failed to save script: {e}")
                    raise
                    
            future = self.api_service.run_async(update_script())
            
            def check_result():
                if future.done():
                    try:
                        script = future.result()
                        self.on_script_saved(script)
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to save script: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
        else:
            # No current script, create new one
            self.new_script()
                
    def delete_script(self) -> None:
        """Delete the selected script."""
        if not self.current_script_id:
            return
            
        current_item = self.script_list.currentItem()
        if not current_item:
            return
            
        script_title = current_item.text().split(" (")[0]  # Remove date if present
        
        reply = QMessageBox.question(
            self,
            "Delete Script",
            f"Are you sure you want to delete '{script_title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info(f"Deleting script ID: {self.current_script_id}")
            
            async def delete():
                try:
                    return await self.api_service.client.delete_script(self.current_script_id)
                except Exception as e:
                    self.logger.error(f"Failed to delete script: {e}")
                    raise
                    
            future = self.api_service.run_async(delete())
            
            def check_result():
                if future.done():
                    try:
                        result = future.result()
                        self.editor_status.setText(f"Deleted: {script_title}")
                        self.current_script_id = None
                        self.text_editor.clear()
                        self.script_title_label.setText("New Script")
                        self.has_unsaved_changes = False
                        self.delete_script_btn.setEnabled(False)
                        # Reload scripts list
                        self.load_scripts()
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to delete script: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
            
    def on_script_selected(self) -> None:
        """Handle script selection from list."""
        current_item = self.script_list.currentItem()
        if current_item and current_item.text() != "(No scripts yet)":
            self.logger.info(f"Script selected: {current_item.text()}")
            # TODO: Load script content in Phase 6
            
    def on_text_changed(self) -> None:
        """Handle text changes in the editor."""
        text = self.text_editor.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.word_count_label.setText(f"Words: {word_count}")
        
    def make_bold(self) -> None:
        """Make selected text bold."""
        # TODO: Implement text formatting in Phase 6
        self.editor_status.setText("Bold formatting will be available in a future update")
        
    def make_italic(self) -> None:
        """Make selected text italic."""
        # TODO: Implement text formatting in Phase 6
        self.editor_status.setText("Italic formatting will be available in a future update")
        
    def show_ai_assist(self) -> None:
        """Show AI assistance dialog."""
        self.logger.info("Showing AI assist")
        
        # Create AI assistant dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Script Assistant")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create AI assistant widget
        ai_assistant = AIAssistantWidget()
        
        # Set current script content
        current_text = self.text_editor.toPlainText()
        if current_text:
            ai_assistant.set_current_script(current_text)
            
        # Connect signals
        ai_assistant.text_generated.connect(self.on_ai_text_generated)
        ai_assistant.text_improved.connect(self.on_ai_text_improved)
        
        layout.addWidget(ai_assistant)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def on_ai_text_generated(self, text: str) -> None:
        """Handle AI-generated text."""
        reply = QMessageBox.question(
            self,
            "Use Generated Script",
            "Do you want to replace the current script with the generated one?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.text_editor.setPlainText(text)
            self.has_unsaved_changes = True
            self.editor_status.setText("Script replaced with AI-generated content *")
            
    def on_ai_text_improved(self, text: str) -> None:
        """Handle AI-improved text."""
        self.text_editor.setPlainText(text)
        self.has_unsaved_changes = True
        self.editor_status.setText("Script updated with AI improvements *")
        
    def generate_speech(self) -> None:
        """Generate speech from the current script."""
        text = self.text_editor.toPlainText().strip()
        if not text:
            self.editor_status.setText("No text to generate speech from")
            return
            
        # Create dialog for TTS settings
        dialog = TTSGenerationDialog(self, text)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            voice_id = dialog.get_voice_id()
            parameters = dialog.get_parameters()
            
            if not voice_id:
                self.editor_status.setText("No voice selected")
                return
                
            self.logger.info(f"Generating speech with voice ID: {voice_id}")
            self.editor_status.setText("Generating speech...")
            
            async def generate():
                try:
                    # Start generation job
                    job = await self.api_service.client.generate_speech(
                        text=text,
                        voice_id=voice_id,
                        parameters=parameters
                    )
                    
                    # Poll for completion
                    while job["status"] in ["pending", "processing"]:
                        await asyncio.sleep(1)
                        job = await self.api_service.client.check_tts_status(job["job_id"])
                        
                    if job["status"] == "completed":
                        # Download the audio file
                        audio_data = await self.api_service.client.download_tts_audio(job["job_id"])
                        return audio_data, job.get("file_path")
                    else:
                        raise Exception(f"Generation failed: {job.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to generate speech: {e}")
                    raise
                    
            future = self.api_service.run_async(generate())
            
            def check_result():
                if future.done():
                    try:
                        audio_data, file_path = future.result()
                        self.editor_status.setText("Speech generated successfully")
                        
                        # Ask user where to save
                        filename, _ = QFileDialog.getSaveFileName(
                            self,
                            "Save Generated Audio",
                            f"script_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                            "Audio Files (*.wav *.mp3);;All Files (*.*)"
                        )
                        
                        if filename:
                            with open(filename, 'wb') as f:
                                f.write(audio_data)
                            self.editor_status.setText(f"Audio saved: {filename}")
                            
                            # Offer to play the audio
                            reply = QMessageBox.question(
                                self,
                                "Play Audio",
                                "Would you like to play the generated audio?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            )
                            
                            if reply == QMessageBox.StandardButton.Yes:
                                try:
                                    from src.utils.audio import AudioPlayer
                                    player = AudioPlayer()
                                    player.load_file(filename)
                                    player.play()
                                except Exception as e:
                                    self.logger.error(f"Failed to play audio: {e}")
                                    QMessageBox.warning(self, "Playback Error", "Could not play the audio file.")
                                    
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to generate speech: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
        
    # Methods for menu actions
    def undo(self) -> None:
        """Undo last edit."""
        self.text_editor.undo()
        
    def redo(self) -> None:
        """Redo last edit."""
        self.text_editor.redo()
        
    def cut(self) -> None:
        """Cut selected text."""
        self.text_editor.cut()
        
    def copy(self) -> None:
        """Copy selected text."""
        self.text_editor.copy()
        
    def paste(self) -> None:
        """Paste from clipboard."""
        self.text_editor.paste()
        
    # API integration methods
    def load_scripts(self) -> None:
        """Load scripts from API."""
        async def load():
            try:
                return await self.api_service.client.list_scripts()
            except Exception as e:
                self.logger.error(f"Failed to load scripts: {e}")
                return None
                
        future = self.api_service.run_async(load())
        
        def check_result():
            if future.done():
                try:
                    result = future.result()
                    if result:
                        self.on_scripts_loaded(result)
                except Exception as e:
                    self.logger.error(f"Failed to load scripts: {e}")
                    self.editor_status.setText("Failed to load scripts")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_scripts_loaded(self, scripts) -> None:
        """Handle loaded scripts."""
        self.script_list.clear()
        
        if not scripts:
            self.script_list.addItem("(No scripts yet)")
            return
            
        # Cache scripts and populate list
        self.scripts_cache = {s.id: s for s in scripts}
        for script in scripts:
            item_text = f"{script.title}"
            if hasattr(script, 'updated_at'):
                item_text += f" ({script.updated_at.strftime('%Y-%m-%d')})"
            self.script_list.addItem(item_text)
            self.script_list.item(self.script_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, script.id
            )
            
    def on_script_created(self, script) -> None:
        """Handle successful script creation."""
        self.logger.info(f"Script created: {script.title} (ID: {script.id})")
        self.current_script_id = script.id
        self.script_title_label.setText(script.title)
        self.text_editor.clear()
        self.has_unsaved_changes = False
        self.editor_status.setText(f"Created: {script.title}")
        # Reload scripts list
        self.load_scripts()
        
    def on_script_saved(self, script) -> None:
        """Handle successful script save."""
        self.logger.info(f"Script saved: {script.title}")
        self.has_unsaved_changes = False
        self.editor_status.setText(f"Saved: {script.title}")
        # Update cache
        self.scripts_cache[script.id] = script
        
    def on_text_changed(self) -> None:
        """Handle text changes in the editor."""
        text = self.text_editor.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.word_count_label.setText(f"Words: {word_count}")
        
        # Mark as having unsaved changes
        if self.current_script_id:
            self.has_unsaved_changes = True
            if not self.editor_status.text().endswith("*"):
                self.editor_status.setText(self.editor_status.text() + " *")
                
    def on_script_selected(self) -> None:
        """Handle script selection from list."""
        current_item = self.script_list.currentItem()
        if current_item and current_item.text() != "(No scripts yet)":
            script_id = current_item.data(Qt.ItemDataRole.UserRole)
            if script_id:
                self.load_script(script_id)
                self.delete_script_btn.setEnabled(True)
        else:
            self.delete_script_btn.setEnabled(False)
            
    def load_script(self, script_id: int) -> None:
        """Load a specific script."""
        self.logger.info(f"Loading script ID: {script_id}")
        
        # Check for unsaved changes
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before loading another script?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_script()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        async def get_script():
            try:
                return await self.api_service.client.get_script(script_id)
            except Exception as e:
                self.logger.error(f"Failed to load script: {e}")
                raise
                
        future = self.api_service.run_async(get_script())
        
        def check_result():
            if future.done():
                try:
                    script = future.result()
                    self.current_script_id = script.id
                    self.script_title_label.setText(script.title)
                    self.text_editor.setPlainText(script.content or "")
                    self.has_unsaved_changes = False
                    self.editor_status.setText(f"Loaded: {script.title}")
                except Exception as e:
                    self.editor_status.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to load script: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def show_script_context_menu(self, pos) -> None:
        """Show context menu for script list."""
        item = self.script_list.itemAt(pos)
        if not item or item.text() == "(No scripts yet)":
            return
            
        script_id = item.data(Qt.ItemDataRole.UserRole)
        if not script_id:
            return
            
        menu = QMenu(self)
        
        # Rename action
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_script(script_id))
        
        # Duplicate action
        duplicate_action = menu.addAction("Duplicate")
        duplicate_action.triggered.connect(lambda: self.duplicate_script(script_id))
        
        # Export action
        export_action = menu.addAction("Export to File")
        export_action.triggered.connect(lambda: self.export_specific_script(script_id))
        
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_specific_script(script_id))
        
        menu.exec(self.script_list.mapToGlobal(pos))
        
    def rename_script(self, script_id: int) -> None:
        """Rename a script."""
        if script_id not in self.scripts_cache:
            return
            
        script = self.scripts_cache[script_id]
        old_title = script.title
        
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Script",
            "Enter new title:",
            text=old_title
        )
        
        if ok and new_title and new_title != old_title:
            async def rename():
                try:
                    return await self.api_service.client.update_script(
                        script_id=script_id,
                        title=new_title
                    )
                except Exception as e:
                    self.logger.error(f"Failed to rename script: {e}")
                    raise
                    
            future = self.api_service.run_async(rename())
            
            def check_result():
                if future.done():
                    try:
                        result = future.result()
                        self.editor_status.setText(f"Renamed: {new_title}")
                        # Update current title if this is the current script
                        if self.current_script_id == script_id:
                            self.script_title_label.setText(new_title)
                        # Reload scripts list
                        self.load_scripts()
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to rename script: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)
            
    def duplicate_script(self, script_id: int) -> None:
        """Duplicate a script."""
        if script_id not in self.scripts_cache:
            return
            
        script = self.scripts_cache[script_id]
        
        async def duplicate():
            try:
                # First get the full script content
                full_script = await self.api_service.client.get_script(script_id)
                # Create new script with copied content
                return await self.api_service.client.create_script(
                    title=f"{script.title} (Copy)",
                    content=full_script.content or ""
                )
            except Exception as e:
                self.logger.error(f"Failed to duplicate script: {e}")
                raise
                
        future = self.api_service.run_async(duplicate())
        
        def check_result():
            if future.done():
                try:
                    result = future.result()
                    self.editor_status.setText(f"Duplicated: {result.title}")
                    # Reload scripts list
                    self.load_scripts()
                except Exception as e:
                    self.editor_status.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to duplicate script: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def export_specific_script(self, script_id: int) -> None:
        """Export a specific script to file."""
        if script_id not in self.scripts_cache:
            return
            
        script = self.scripts_cache[script_id]
        
        async def get_content():
            try:
                return await self.api_service.client.get_script(script_id)
            except Exception as e:
                self.logger.error(f"Failed to get script content: {e}")
                raise
                
        future = self.api_service.run_async(get_content())
        
        def check_result():
            if future.done():
                try:
                    full_script = future.result()
                    
                    # Clean filename
                    clean_title = "".join(c for c in script.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    
                    filename, _ = QFileDialog.getSaveFileName(
                        self,
                        "Export Script",
                        f"{clean_title}.txt",
                        "Text Files (*.txt);;All Files (*.*)"
                    )
                    
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(full_script.content or "")
                        self.editor_status.setText(f"Exported: {filename}")
                        self.logger.info(f"Exported script to: {filename}")
                        
                except Exception as e:
                    self.editor_status.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to export script: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def delete_specific_script(self, script_id: int) -> None:
        """Delete a specific script from context menu."""
        if script_id not in self.scripts_cache:
            return
            
        script = self.scripts_cache[script_id]
        
        reply = QMessageBox.question(
            self,
            "Delete Script",
            f"Are you sure you want to delete '{script.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            async def delete():
                try:
                    return await self.api_service.client.delete_script(script_id)
                except Exception as e:
                    self.logger.error(f"Failed to delete script: {e}")
                    raise
                    
            future = self.api_service.run_async(delete())
            
            def check_result():
                if future.done():
                    try:
                        result = future.result()
                        self.editor_status.setText(f"Deleted: {script.title}")
                        # Clear editor if this was the current script
                        if self.current_script_id == script_id:
                            self.current_script_id = None
                            self.text_editor.clear()
                            self.script_title_label.setText("New Script")
                            self.has_unsaved_changes = False
                            self.delete_script_btn.setEnabled(False)
                        # Reload scripts list
                        self.load_scripts()
                    except Exception as e:
                        self.editor_status.setText(f"Error: {str(e)}")
                        QMessageBox.critical(self, "Error", f"Failed to delete script: {str(e)}")
                else:
                    QTimer.singleShot(50, check_result)
                    
            QTimer.singleShot(0, check_result)


class TTSGenerationDialog(QDialog):
    """Dialog for TTS generation settings."""
    
    def __init__(self, parent, text: str):
        """Initialize TTS generation dialog."""
        super().__init__(parent)
        self.text = text
        self.voice_id = None
        self.api_service = get_api_service()
        self.voice_profiles = []
        
        self.setWindowTitle("Generate Speech")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_voices()
        
    def init_ui(self) -> None:
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Text preview
        preview_group = QGroupBox("Text Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_text = QTextEdit()
        preview_text.setPlainText(self.text[:200] + "..." if len(self.text) > 200 else self.text)
        preview_text.setReadOnly(True)
        preview_text.setMaximumHeight(100)
        preview_layout.addWidget(preview_text)
        layout.addWidget(preview_group)
        
        # Voice selection
        voice_group = QGroupBox("Voice Selection")
        voice_layout = QVBoxLayout(voice_group)
        
        self.voice_combo = QComboBox()
        self.voice_combo.addItem("Loading voices...")
        voice_layout.addWidget(QLabel("Select Voice:"))
        voice_layout.addWidget(self.voice_combo)
        layout.addWidget(voice_group)
        
        # TTS Parameters
        params_group = QGroupBox("Speech Parameters")
        params_layout = QFormLayout(params_group)
        
        # Speed
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 200)
        self.speed_spin.setValue(100)
        self.speed_spin.setSuffix("%")
        params_layout.addRow("Speed:", self.speed_spin)
        
        # Pitch
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_label = QLabel("0")
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        params_layout.addRow("Pitch:", pitch_layout)
        
        # Emotion
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["Neutral", "Happy", "Sad", "Angry", "Surprised"])
        params_layout.addRow("Emotion:", self.emotion_combo)
        
        layout.addWidget(params_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_voices(self) -> None:
        """Load available voice profiles."""
        async def load():
            try:
                profiles = await self.api_service.client.list_voice_profiles()
                return [p for p in profiles if p.get("is_cloned", False)]
            except Exception:
                return []
                
        future = self.api_service.run_async(load())
        
        def check_result():
            if future.done():
                try:
                    self.voice_profiles = future.result()
                    self.voice_combo.clear()
                    
                    if self.voice_profiles:
                        for profile in self.voice_profiles:
                            self.voice_combo.addItem(profile["name"], profile["id"])
                    else:
                        self.voice_combo.addItem("No cloned voices available")
                except Exception:
                    self.voice_combo.clear()
                    self.voice_combo.addItem("Failed to load voices")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def get_voice_id(self) -> Optional[int]:
        """Get selected voice ID."""
        if self.voice_combo.currentData():
            return self.voice_combo.currentData()
        return None
        
    def get_parameters(self) -> Dict:
        """Get TTS parameters."""
        return {
            "speed": self.speed_spin.value() / 100.0,
            "pitch": self.pitch_slider.value() / 50.0,
            "emotion": self.emotion_combo.currentText().lower()
        }
