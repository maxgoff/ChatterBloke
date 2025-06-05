"""AI dialogue generation assistant."""

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.dialogue.tabs.dialogue_editor import DialogueLine
from src.gui.services import APIService


class AIDialogueAssistant(QDialog):
    """AI assistant for generating dialogue."""
    
    def __init__(self, api_service: APIService, script_type: str, 
                 speaker_a: str, speaker_b: str, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.script_type = script_type
        self.speaker_a = speaker_a
        self.speaker_b = speaker_b
        self.logger = logging.getLogger(__name__)
        
        self.generated_lines: List[DialogueLine] = []
        
        self.setWindowTitle("AI Dialogue Assistant")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Settings group
        settings_group = QGroupBox("Dialogue Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Topic/prompt
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("Topic/Prompt:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText(f"Enter the topic for the {self.script_type.lower()}...")
        topic_layout.addWidget(self.topic_input)
        settings_layout.addLayout(topic_layout)
        
        # Tone
        tone_layout = QHBoxLayout()
        tone_layout.addWidget(QLabel("Tone:"))
        self.tone_combo = QComboBox()
        self.tone_combo.addItems([
            "Professional", "Casual", "Humorous", "Serious", 
            "Educational", "Argumentative", "Friendly"
        ])
        tone_layout.addWidget(self.tone_combo)
        
        # Number of exchanges
        tone_layout.addWidget(QLabel("Exchanges:"))
        self.exchanges_spin = QSpinBox()
        self.exchanges_spin.setRange(1, 20)
        self.exchanges_spin.setValue(5)
        self.exchanges_spin.setToolTip("Number of back-and-forth exchanges")
        tone_layout.addWidget(self.exchanges_spin)
        
        settings_layout.addLayout(tone_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["ollama (local)", "openai", "claude"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        settings_layout.addLayout(model_layout)
        
        layout.addWidget(settings_group)
        
        # Generate button
        self.generate_btn = QPushButton("🤖 Generate Dialogue")
        self.generate_btn.clicked.connect(self.generate_dialogue)
        layout.addWidget(self.generate_btn)
        
        # Preview area
        preview_group = QGroupBox("Generated Dialogue Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group, 1)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def generate_dialogue(self) -> None:
        """Generate dialogue using AI."""
        topic = self.topic_input.text().strip()
        if not topic:
            self.preview_text.setPlainText("Please enter a topic or prompt.")
            return
            
        # Build prompt based on script type
        if self.script_type == "Debate":
            prompt = f"""Generate a debate between two speakers on the topic: {topic}
Speaker A ({self.speaker_a}) argues FOR the topic.
Speaker B ({self.speaker_b}) argues AGAINST the topic.
Tone: {self.tone_combo.currentText()}
Number of exchanges: {self.exchanges_spin.value()}

Format each line as:
SPEAKER_NAME: Their dialogue

Example:
{self.speaker_a}: I believe that {topic} is essential because...
{self.speaker_b}: I respectfully disagree. The evidence shows..."""

        elif self.script_type == "Comedy Sketch":
            prompt = f"""Generate a funny comedy sketch between two comedians about: {topic}
Speaker A: {self.speaker_a}
Speaker B: {self.speaker_b}
Tone: {self.tone_combo.currentText()} comedy
Number of exchanges: {self.exchanges_spin.value()}

Make it humorous with jokes, puns, and comedic timing.
Format each line as:
SPEAKER_NAME: Their dialogue"""

        elif self.script_type == "Blog Review":
            prompt = f"""Generate a conversation where {self.speaker_a} reviews a blog post about: {topic}
{self.speaker_b} is the blog author responding to questions and feedback.
Tone: {self.tone_combo.currentText()}
Number of exchanges: {self.exchanges_spin.value()}

Format each line as:
SPEAKER_NAME: Their dialogue"""

        else:  # Regular dialogue
            prompt = f"""Generate a natural conversation between two people about: {topic}
Speaker A: {self.speaker_a}
Speaker B: {self.speaker_b}
Tone: {self.tone_combo.currentText()}
Number of exchanges: {self.exchanges_spin.value()}

Format each line as:
SPEAKER_NAME: Their dialogue"""

        # Show generating status
        self.preview_text.setPlainText("Generating dialogue... Please wait...")
        self.generate_btn.setEnabled(False)
        
        # For now, create sample dialogue
        # TODO: Integrate with actual LLM API
        self.create_sample_dialogue(topic)
        
    def create_sample_dialogue(self, topic: str) -> None:
        """Create sample dialogue for testing."""
        self.generated_lines.clear()
        
        if self.script_type == "Debate":
            dialogues = [
                (self.speaker_a, f"I strongly believe that {topic} is crucial for our future. The evidence clearly shows its positive impact on society."),
                (self.speaker_b, f"While I understand your position, I must disagree. {topic} has several concerning drawbacks that we cannot ignore."),
                (self.speaker_a, "Could you elaborate on these drawbacks? I'd like to address your concerns with factual data."),
                (self.speaker_b, "Certainly. First, the economic implications are significant. Studies indicate substantial costs without guaranteed benefits."),
                (self.speaker_a, "That's a fair point, but we must consider the long-term benefits versus short-term costs. Innovation always requires initial investment."),
            ]
        elif self.script_type == "Comedy Sketch":
            dialogues = [
                (self.speaker_a, f"So I was thinking about {topic} the other day, and it hit me - this is either genius or completely insane!"),
                (self.speaker_b, "Knowing you, it's probably both! Remember your last 'genius' idea with the rubber duck?"),
                (self.speaker_a, "Hey, that duck was revolutionary! It just wasn't ready for mainstream society."),
                (self.speaker_b, "Right, because society wasn't ready for a duck that screams motivational quotes at 3 AM!"),
                (self.speaker_a, f"Exactly! But seriously, about {topic} - imagine the possibilities!"),
            ]
        else:
            dialogues = [
                (self.speaker_a, f"I've been thinking about {topic} lately. What's your take on it?"),
                (self.speaker_b, f"It's interesting you bring that up. I've had some experience with {topic} recently."),
                (self.speaker_a, "Really? I'd love to hear about your experience. What stood out to you?"),
                (self.speaker_b, "Well, the most surprising aspect was how it challenged my initial assumptions."),
                (self.speaker_a, "That's fascinating. Could you give me a specific example?"),
            ]
            
        # Add lines based on requested exchanges
        for i in range(min(self.exchanges_spin.value(), len(dialogues))):
            speaker, text = dialogues[i]
            self.generated_lines.append(DialogueLine(speaker, text))
            
        # Display preview
        self.update_preview()
        self.generate_btn.setEnabled(True)
        
    def update_preview(self) -> None:
        """Update the preview display."""
        text_parts = []
        for line in self.generated_lines:
            text_parts.append(f"{line.speaker}: {line.text}")
            
        self.preview_text.setPlainText('\n\n'.join(text_parts))
        
    def get_generated_dialogue(self) -> List[DialogueLine]:
        """Get the generated dialogue lines."""
        return self.generated_lines