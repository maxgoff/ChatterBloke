"""AI Assistant widget for script improvement."""

import logging
from typing import Optional, List, Dict

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QTabWidget,
    QGroupBox,
    QSlider,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QMessageBox,
    QProgressBar,
    QButtonGroup,
    QRadioButton,
    QApplication,
)

from src.gui.services import get_api_service


logger = logging.getLogger(__name__)


class AIAssistantWidget(QWidget):
    """AI Assistant widget for script generation and improvement."""
    
    # Signals
    text_generated = pyqtSignal(str)  # Emitted when new text is generated
    text_improved = pyqtSignal(str)   # Emitted when text is improved
    
    def __init__(self):
        """Initialize the AI Assistant widget."""
        super().__init__()
        self.api_service = get_api_service()
        self.available_models = []
        self.current_script = ""
        
        self.init_ui()
        self.load_models()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("AI Assistant"))
        header_layout.addStretch()
        
        # Model selection
        header_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(150)
        header_layout.addWidget(self.model_combo)
        
        # Refresh models button
        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(30)
        refresh_btn.setToolTip("Refresh available models")
        refresh_btn.clicked.connect(self.load_models)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Create tabs for different functions
        self.tabs = QTabWidget()
        
        # Generate tab
        self.generate_tab = self.create_generate_tab()
        self.tabs.addTab(self.generate_tab, "Generate")
        
        # Improve tab
        self.improve_tab = self.create_improve_tab()
        self.tabs.addTab(self.improve_tab, "Improve")
        
        # Grammar tab
        self.grammar_tab = self.create_grammar_tab()
        self.tabs.addTab(self.grammar_tab, "Grammar")
        
        # Suggestions tab
        self.suggestions_tab = self.create_suggestions_tab()
        self.tabs.addTab(self.suggestions_tab, "Suggestions")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px;"
        )
        layout.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
    def create_generate_tab(self) -> QWidget:
        """Create the generate script tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Script type selection
        type_group = QGroupBox("Script Type")
        type_layout = QVBoxLayout(type_group)
        
        self.script_type_group = QButtonGroup()
        script_types = [
            ("General", "general"),
            ("Presentation", "presentation"),
            ("Video", "video"),
            ("Podcast", "podcast"),
            ("Educational", "educational"),
        ]
        
        for label, value in script_types:
            radio = QRadioButton(label)
            radio.setProperty("script_type", value)
            self.script_type_group.addButton(radio)
            type_layout.addWidget(radio)
            if value == "general":
                radio.setChecked(True)
                
        layout.addWidget(type_group)
        
        # Prompt input
        layout.addWidget(QLabel("Describe what you want to create:"))
        self.generate_prompt = QTextEdit()
        self.generate_prompt.setPlaceholderText(
            "Example: Create a 5-minute presentation about climate change "
            "for a high school audience..."
        )
        self.generate_prompt.setMaximumHeight(150)
        layout.addWidget(self.generate_prompt)
        
        # Temperature control
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Creativity:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 20)  # 0.0 to 2.0
        self.temp_slider.setValue(7)  # 0.7
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(5)
        temp_layout.addWidget(self.temp_slider)
        self.temp_label = QLabel("0.7")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v/10:.1f}")
        )
        temp_layout.addWidget(self.temp_label)
        temp_layout.addStretch()
        layout.addLayout(temp_layout)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Script")
        self.generate_btn.clicked.connect(self.generate_script)
        layout.addWidget(self.generate_btn)
        
        # Result display
        layout.addWidget(QLabel("Generated Script:"))
        self.generate_result = QTextEdit()
        self.generate_result.setReadOnly(True)
        layout.addWidget(self.generate_result)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        use_btn = QPushButton("Use This Script")
        use_btn.clicked.connect(self.use_generated_script)
        action_layout.addWidget(use_btn)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_generated_to_clipboard)
        action_layout.addWidget(copy_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        return widget
        
    def create_improve_tab(self) -> QWidget:
        """Create the improve script tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        layout.addWidget(QLabel("Improvement Instructions:"))
        self.improve_instructions = QTextEdit()
        self.improve_instructions.setPlaceholderText(
            "Example: Make this more engaging, add humor, "
            "and reduce the length by 20%..."
        )
        self.improve_instructions.setMaximumHeight(100)
        layout.addWidget(self.improve_instructions)
        
        # Current script display
        layout.addWidget(QLabel("Current Script:"))
        self.improve_current = QTextEdit()
        self.improve_current.setReadOnly(True)
        self.improve_current.setMaximumHeight(150)
        layout.addWidget(self.improve_current)
        
        # Improve button
        self.improve_btn = QPushButton("Improve Script")
        self.improve_btn.clicked.connect(self.improve_script)
        layout.addWidget(self.improve_btn)
        
        # Result display
        layout.addWidget(QLabel("Improved Script:"))
        self.improve_result = QTextEdit()
        self.improve_result.setReadOnly(True)
        layout.addWidget(self.improve_result)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Improvements")
        apply_btn.clicked.connect(self.apply_improvements)
        action_layout.addWidget(apply_btn)
        
        compare_btn = QPushButton("Compare Versions")
        compare_btn.clicked.connect(self.compare_versions)
        action_layout.addWidget(compare_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        return widget
        
    def create_grammar_tab(self) -> QWidget:
        """Create the grammar check tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Check button
        self.grammar_check_btn = QPushButton("Check Grammar")
        self.grammar_check_btn.clicked.connect(self.check_grammar)
        layout.addWidget(self.grammar_check_btn)
        
        # Issues list
        layout.addWidget(QLabel("Issues Found:"))
        self.issues_list = QListWidget()
        self.issues_list.setMaximumHeight(150)
        layout.addWidget(self.issues_list)
        
        # Corrected text
        layout.addWidget(QLabel("Corrected Text:"))
        self.grammar_result = QTextEdit()
        self.grammar_result.setReadOnly(True)
        layout.addWidget(self.grammar_result)
        
        # Apply corrections button
        self.apply_grammar_btn = QPushButton("Apply Corrections")
        self.apply_grammar_btn.clicked.connect(self.apply_grammar_corrections)
        self.apply_grammar_btn.setEnabled(False)
        layout.addWidget(self.apply_grammar_btn)
        
        return widget
        
    def create_suggestions_tab(self) -> QWidget:
        """Create the suggestions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Focus areas
        layout.addWidget(QLabel("Get suggestions for:"))
        
        self.focus_checkboxes = {}
        focus_areas = [
            ("Clarity", "clarity"),
            ("Engagement", "engagement"),
            ("Pacing", "pacing"),
            ("Structure", "structure"),
            ("Conciseness", "conciseness"),
            ("Tone", "tone"),
        ]
        
        checkbox_layout = QHBoxLayout()
        for label, value in focus_areas:
            checkbox = QCheckBox(label)
            checkbox.setProperty("focus_area", value)
            self.focus_checkboxes[value] = checkbox
            checkbox_layout.addWidget(checkbox)
            if value in ["clarity", "engagement", "pacing"]:
                checkbox.setChecked(True)
                
        layout.addLayout(checkbox_layout)
        
        # Get suggestions button
        self.suggest_btn = QPushButton("Get Suggestions")
        self.suggest_btn.clicked.connect(self.get_suggestions)
        layout.addWidget(self.suggest_btn)
        
        # Suggestions display
        self.suggestions_list = QListWidget()
        layout.addWidget(self.suggestions_list)
        
        return widget
        
    def set_current_script(self, text: str):
        """Set the current script text for improvement."""
        self.current_script = text
        self.improve_current.setPlainText(text[:500] + "..." if len(text) > 500 else text)
        
    def load_models(self):
        """Load available LLM models."""
        async def load():
            try:
                return await self.api_service.client.list_llm_models()
            except Exception as e:
                logger.error(f"Failed to load models: {e}")
                return []
                
        future = self.api_service.run_async(load())
        
        def check_result():
            if future.done():
                try:
                    models = future.result()
                    self.on_models_loaded(models)
                except Exception as e:
                    logger.error(f"Failed to load models: {e}")
                    self.status_label.setText("Failed to load models")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_models_loaded(self, models: List[str]):
        """Handle loaded models."""
        self.available_models = models
        self.model_combo.clear()
        
        if models:
            self.model_combo.addItems(models)
        else:
            self.model_combo.addItem("(No models available)")
            
    def generate_script(self):
        """Generate a new script."""
        prompt = self.generate_prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "No Prompt", "Please enter a prompt for script generation.")
            return
            
        # Get selected script type
        script_type = "general"
        checked_btn = self.script_type_group.checkedButton()
        if checked_btn:
            script_type = checked_btn.property("script_type")
            
        model = self.model_combo.currentText()
        if model == "(No models available)":
            model = None
            
        temperature = self.temp_slider.value() / 10.0
        
        self.show_progress("Generating script...")
        
        async def generate():
            try:
                return await self.api_service.client.generate_script_with_llm(
                    prompt=prompt,
                    script_type=script_type,
                    model=model,
                    temperature=temperature,
                )
            except Exception as e:
                logger.error(f"Failed to generate script: {e}")
                raise
                
        future = self.api_service.run_async(generate())
        
        def check_result():
            if future.done():
                self.hide_progress()
                try:
                    result = future.result()
                    self.generate_result.setPlainText(result)
                    self.status_label.setText("Script generated successfully")
                except Exception as e:
                    self.status_label.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to generate script: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def improve_script(self):
        """Improve the current script."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script loaded for improvement.")
            return
            
        instructions = self.improve_instructions.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(self, "No Instructions", "Please provide improvement instructions.")
            return
            
        model = self.model_combo.currentText()
        if model == "(No models available)":
            model = None
            
        self.show_progress("Improving script...")
        
        async def improve():
            try:
                return await self.api_service.client.improve_script_with_llm(
                    script=self.current_script,
                    instructions=instructions,
                    model=model,
                )
            except Exception as e:
                logger.error(f"Failed to improve script: {e}")
                raise
                
        future = self.api_service.run_async(improve())
        
        def check_result():
            if future.done():
                self.hide_progress()
                try:
                    result = future.result()
                    self.improve_result.setPlainText(result)
                    self.status_label.setText("Script improved successfully")
                except Exception as e:
                    self.status_label.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to improve script: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def check_grammar(self):
        """Check grammar of the current script."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script loaded for grammar check.")
            return
            
        model = self.model_combo.currentText()
        if model == "(No models available)":
            model = None
            
        self.show_progress("Checking grammar...")
        
        async def check():
            try:
                response = await self.api_service.client._request(
                    "POST",
                    "/api/llm/check-grammar",
                    params={"text": self.current_script, "model": model}
                )
                return response
            except Exception as e:
                logger.error(f"Failed to check grammar: {e}")
                raise
                
        future = self.api_service.run_async(check())
        
        def check_result():
            if future.done():
                self.hide_progress()
                try:
                    result = future.result()
                    self.on_grammar_checked(result)
                except Exception as e:
                    self.status_label.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to check grammar: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_grammar_checked(self, result: Dict):
        """Handle grammar check results."""
        self.issues_list.clear()
        
        issues = result.get("issues", [])
        if issues:
            for issue in issues:
                self.issues_list.addItem(issue)
            self.status_label.setText(f"Found {len(issues)} grammar issues")
        else:
            self.issues_list.addItem("No grammar issues found!")
            self.status_label.setText("Grammar check complete - no issues found")
            
        corrected_text = result.get("corrected_text", self.current_script)
        self.grammar_result.setPlainText(corrected_text)
        
        # Enable apply button if there are corrections
        self.apply_grammar_btn.setEnabled(result.get("has_issues", False))
        
    def get_suggestions(self):
        """Get improvement suggestions."""
        if not self.current_script:
            QMessageBox.warning(self, "No Script", "No script loaded for suggestions.")
            return
            
        # Get selected focus areas
        focus_areas = []
        for area, checkbox in self.focus_checkboxes.items():
            if checkbox.isChecked():
                focus_areas.append(area)
                
        if not focus_areas:
            QMessageBox.warning(self, "No Areas Selected", "Please select at least one area for suggestions.")
            return
            
        model = self.model_combo.currentText()
        if model == "(No models available)":
            model = None
            
        self.show_progress("Getting suggestions...")
        
        async def suggest():
            try:
                response = await self.api_service.client._request(
                    "POST",
                    "/api/llm/suggest",
                    json={
                        "script": self.current_script,
                        "focus_areas": focus_areas,
                        "model": model
                    }
                )
                return response
            except Exception as e:
                logger.error(f"Failed to get suggestions: {e}")
                raise
                
        future = self.api_service.run_async(suggest())
        
        def check_result():
            if future.done():
                self.hide_progress()
                try:
                    result = future.result()
                    self.on_suggestions_received(result)
                except Exception as e:
                    self.status_label.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to get suggestions: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_suggestions_received(self, result: Dict):
        """Handle received suggestions."""
        self.suggestions_list.clear()
        
        suggestions = result.get("suggestions", [])
        for suggestion in suggestions:
            area = suggestion.get("area", "Unknown")
            text = suggestion.get("suggestion", "")
            
            item = QListWidgetItem(f"[{area.title()}]\n{text}")
            item.setData(Qt.ItemDataRole.UserRole, suggestion)
            self.suggestions_list.addItem(item)
            
        self.status_label.setText(f"Received {len(suggestions)} suggestions")
        
    def use_generated_script(self):
        """Use the generated script."""
        text = self.generate_result.toPlainText()
        if text:
            self.text_generated.emit(text)
            self.status_label.setText("Script sent to editor")
            
    def copy_generated_to_clipboard(self):
        """Copy generated script to clipboard."""
        text = self.generate_result.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText("Copied to clipboard")
            
    def apply_improvements(self):
        """Apply the improved script."""
        text = self.improve_result.toPlainText()
        if text:
            self.text_improved.emit(text)
            self.status_label.setText("Improvements applied")
            
    def apply_grammar_corrections(self):
        """Apply grammar corrections."""
        text = self.grammar_result.toPlainText()
        if text:
            self.text_improved.emit(text)
            self.status_label.setText("Grammar corrections applied")
            self.apply_grammar_btn.setEnabled(False)
            
    def compare_versions(self):
        """Compare original and improved versions."""
        # TODO: Implement diff visualization
        QMessageBox.information(
            self,
            "Compare Versions",
            "Version comparison will be implemented in a future update."
        )
        
    def show_progress(self, message: str):
        """Show progress indicator."""
        self.status_label.setText(message)
        self.progress_bar.show()
        self.setEnabled(False)
        
    def hide_progress(self):
        """Hide progress indicator."""
        self.progress_bar.hide()
        self.setEnabled(True)