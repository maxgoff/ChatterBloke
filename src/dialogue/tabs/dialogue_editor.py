"""Dialogue editor tab for creating and editing two-speaker conversations."""

import json
import logging
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.services import APIService


class DialogueLine:
    """Represents a single line of dialogue."""
    
    def __init__(self, speaker: str, text: str):
        self.speaker = speaker
        self.text = text
        
    def to_dict(self) -> Dict:
        return {"speaker": self.speaker, "text": self.text}
        
    @classmethod
    def from_dict(cls, data: Dict) -> "DialogueLine":
        return cls(data["speaker"], data["text"])


class DialogueEditorTab(QWidget):
    """Tab for editing dialogue scripts."""
    
    dialogue_changed = pyqtSignal()
    
    def __init__(self, api_service: APIService):
        super().__init__()
        self.api_service = api_service
        self.logger = logging.getLogger(__name__)
        
        self.dialogue_lines: List[DialogueLine] = []
        self.current_project_id: Optional[int] = None
        self.current_script_id: Optional[int] = None
        self._has_unsaved_changes = False
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_layout.addWidget(QLabel("Script Type:"))
        self.script_type_combo = QComboBox()
        self.script_type_combo.addItems(["Dialogue", "Debate", "Comedy Sketch", "Blog Review"])
        self.script_type_combo.currentTextChanged.connect(self.on_script_type_changed)
        header_layout.addWidget(self.script_type_combo)
        
        header_layout.addWidget(QLabel("Speaker A:"))
        self.speaker_a_name = QLineEdit()
        self.speaker_a_name.setText("Speaker A")
        self.speaker_a_name.textChanged.connect(self.on_speaker_name_changed)
        header_layout.addWidget(self.speaker_a_name)
        
        header_layout.addWidget(QLabel("Speaker B:"))
        self.speaker_b_name = QLineEdit()
        self.speaker_b_name.setText("Speaker B")
        self.speaker_b_name.textChanged.connect(self.on_speaker_name_changed)
        header_layout.addWidget(self.speaker_b_name)
        
        header_layout.addStretch()
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        header_layout.addWidget(self.char_count_label)
        
        layout.addLayout(header_layout)
        
        # Main editor area
        self.editor = DialogueTextEdit()
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.setFont(QFont("Courier", 11))
        layout.addWidget(self.editor, 1)
        
        # Bottom toolbar
        toolbar_layout = QHBoxLayout()
        
        # Add line button
        self.add_line_btn = QPushButton("➕ Add Line")
        self.add_line_btn.clicked.connect(self.add_dialogue_line)
        toolbar_layout.addWidget(self.add_line_btn)
        
        # Switch speaker button
        self.switch_speaker_btn = QPushButton("🔄 Switch Speaker")
        self.switch_speaker_btn.clicked.connect(self.switch_current_speaker)
        toolbar_layout.addWidget(self.switch_speaker_btn)
        
        toolbar_layout.addStretch()
        
        # Format buttons
        self.format_btn = QPushButton("📋 Format")
        self.format_btn.setToolTip("Format dialogue with proper spacing")
        self.format_btn.clicked.connect(self.format_dialogue)
        toolbar_layout.addWidget(self.format_btn)
        
        # AI assist button
        self.ai_assist_btn = QPushButton("🤖 AI Assist")
        self.ai_assist_btn.setToolTip("Generate dialogue with AI")
        self.ai_assist_btn.clicked.connect(self.show_ai_assistant)
        toolbar_layout.addWidget(self.ai_assist_btn)
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_dialogue)
        toolbar_layout.addWidget(self.clear_btn)
        
        layout.addLayout(toolbar_layout)
        
    def on_script_type_changed(self, script_type: str) -> None:
        """Handle script type change."""
        self.mark_as_changed()
        
        # Update speaker names based on type
        if script_type == "Debate":
            self.speaker_a_name.setText("Pro")
            self.speaker_b_name.setText("Con")
        elif script_type == "Blog Review":
            self.speaker_a_name.setText("Reviewer")
            self.speaker_b_name.setText("Author")
        elif script_type == "Comedy Sketch":
            self.speaker_a_name.setText("Comedian A")
            self.speaker_b_name.setText("Comedian B")
        else:
            self.speaker_a_name.setText("Speaker A")
            self.speaker_b_name.setText("Speaker B")
            
    def on_speaker_name_changed(self) -> None:
        """Handle speaker name change."""
        self.mark_as_changed()
        self.update_dialogue_display()
        
    def on_text_changed(self) -> None:
        """Handle text change in editor."""
        self.mark_as_changed()
        self.update_character_count()
        self.parse_dialogue_from_text()
        
    def update_character_count(self) -> None:
        """Update character count display."""
        text = self.editor.toPlainText()
        self.char_count_label.setText(f"{len(text)} characters")
        
    def parse_dialogue_from_text(self) -> None:
        """Parse dialogue lines from editor text."""
        text = self.editor.toPlainText()
        lines = text.strip().split('\n')
        
        self.dialogue_lines.clear()
        
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    dialogue = parts[1].strip()
                    if speaker and dialogue:
                        self.dialogue_lines.append(DialogueLine(speaker, dialogue))
                        
    def update_dialogue_display(self) -> None:
        """Update the editor display with formatted dialogue."""
        if not self.dialogue_lines:
            return
            
        # Temporarily disconnect to avoid recursion
        self.editor.textChanged.disconnect()
        
        cursor_pos = self.editor.textCursor().position()
        
        text_parts = []
        for line in self.dialogue_lines:
            # Map generic speaker names to custom names
            speaker = line.speaker
            if speaker in ["Speaker A", "Pro", "Reviewer", "Comedian A"]:
                speaker = self.speaker_a_name.text()
            elif speaker in ["Speaker B", "Con", "Author", "Comedian B"]:
                speaker = self.speaker_b_name.text()
                
            text_parts.append(f"{speaker}: {line.text}")
            
        self.editor.setPlainText('\n\n'.join(text_parts))
        
        # Restore cursor position
        cursor = self.editor.textCursor()
        cursor.setPosition(min(cursor_pos, len(self.editor.toPlainText())))
        self.editor.setTextCursor(cursor)
        
        # Reconnect
        self.editor.textChanged.connect(self.on_text_changed)
        
    def add_dialogue_line(self) -> None:
        """Add a new dialogue line."""
        # Determine current speaker
        if self.dialogue_lines:
            last_speaker = self.dialogue_lines[-1].speaker
            if last_speaker in [self.speaker_a_name.text(), "Speaker A", "Pro", "Reviewer", "Comedian A"]:
                next_speaker = self.speaker_b_name.text()
            else:
                next_speaker = self.speaker_a_name.text()
        else:
            next_speaker = self.speaker_a_name.text()
            
        # Add to editor
        current_text = self.editor.toPlainText()
        if current_text and not current_text.endswith('\n'):
            current_text += '\n\n'
        current_text += f"{next_speaker}: "
        
        self.editor.setPlainText(current_text)
        self.editor.moveCursor(self.editor.textCursor().End)
        self.editor.setFocus()
        
    def switch_current_speaker(self) -> None:
        """Switch the current line's speaker."""
        cursor = self.editor.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        line = cursor.selectedText()
        
        if ':' in line:
            parts = line.split(':', 1)
            current_speaker = parts[0].strip()
            dialogue = parts[1].strip()
            
            # Switch speaker
            if current_speaker == self.speaker_a_name.text():
                new_speaker = self.speaker_b_name.text()
            else:
                new_speaker = self.speaker_a_name.text()
                
            # Replace line
            cursor.insertText(f"{new_speaker}: {dialogue}")
            
    def format_dialogue(self) -> None:
        """Format dialogue with proper spacing."""
        self.parse_dialogue_from_text()
        self.update_dialogue_display()
        
    def clear_dialogue(self) -> None:
        """Clear all dialogue."""
        reply = QMessageBox.question(
            self,
            "Clear Dialogue",
            "Are you sure you want to clear all dialogue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.editor.clear()
            self.dialogue_lines.clear()
            self.mark_as_changed()
            
    def show_ai_assistant(self) -> None:
        """Show AI dialogue generation assistant."""
        from src.dialogue.widgets.ai_dialogue_assistant import AIDialogueAssistant
        
        dialog = AIDialogueAssistant(
            self.api_service,
            self.script_type_combo.currentText(),
            self.speaker_a_name.text(),
            self.speaker_b_name.text(),
            self
        )
        
        if dialog.exec():
            generated_lines = dialog.get_generated_dialogue()
            if generated_lines:
                # Add generated lines
                for line in generated_lines:
                    self.dialogue_lines.append(line)
                self.update_dialogue_display()
                self.mark_as_changed()
                
    def new_dialogue(self) -> None:
        """Create a new dialogue."""
        if self._has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before creating new dialogue?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_dialogue()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        # Clear everything
        self.editor.clear()
        self.dialogue_lines.clear()
        self.current_project_id = None
        self.current_script_id = None
        self._has_unsaved_changes = False
        self.script_type_combo.setCurrentIndex(0)
        
    def save_dialogue(self) -> None:
        """Save current dialogue."""
        # This will be implemented when we add project management
        self.logger.info("Saving dialogue...")
        self._has_unsaved_changes = False
        
    def export_script(self) -> None:
        """Export dialogue as text file."""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Script",
            "dialogue_script.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "Success", "Script exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export script: {e}")
                
    def get_dialogue(self) -> Optional[Dict]:
        """Get current dialogue data."""
        if not self.dialogue_lines:
            return None
            
        return {
            "script_type": self.script_type_combo.currentText().lower().replace(' ', '_'),
            "speaker_a": self.speaker_a_name.text(),
            "speaker_b": self.speaker_b_name.text(),
            "lines": [line.to_dict() for line in self.dialogue_lines]
        }
        
    def set_dialogue(self, dialogue_data: Dict) -> None:
        """Set dialogue from data."""
        self.dialogue_lines.clear()
        
        # Set script type
        script_type = dialogue_data.get("script_type", "dialogue")
        script_type = script_type.replace('_', ' ').title()
        index = self.script_type_combo.findText(script_type)
        if index >= 0:
            self.script_type_combo.setCurrentIndex(index)
            
        # Set speaker names
        self.speaker_a_name.setText(dialogue_data.get("speaker_a", "Speaker A"))
        self.speaker_b_name.setText(dialogue_data.get("speaker_b", "Speaker B"))
        
        # Set lines
        for line_data in dialogue_data.get("lines", []):
            self.dialogue_lines.append(DialogueLine.from_dict(line_data))
            
        self.update_dialogue_display()
        self._has_unsaved_changes = False
        
    def mark_as_changed(self) -> None:
        """Mark dialogue as having unsaved changes."""
        self._has_unsaved_changes = True
        self.dialogue_changed.emit()
        
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._has_unsaved_changes
        
    def undo(self) -> None:
        """Undo last edit."""
        self.editor.undo()
        
    def redo(self) -> None:
        """Redo last undone edit."""
        self.editor.redo()
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("Dialogue editor cleanup")


class DialogueTextEdit(QTextEdit):
    """Custom text editor for dialogue with syntax highlighting."""
    
    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        
        
# Import QLineEdit that was missing
from PyQt6.QtWidgets import QLineEdit