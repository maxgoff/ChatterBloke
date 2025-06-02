"""Fullscreen teleprompter window."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
)

from src.gui.widgets.teleprompter_display import TeleprompterDisplay


class TeleprompterWindow(QMainWindow):
    """Fullscreen window for teleprompter display."""
    
    # Signals
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the teleprompter window."""
        super().__init__(parent)
        self.is_playing = False
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.auto_scroll)
        self.scroll_speed = 5
        
        self.setWindowTitle("Teleprompter")
        self.setStyleSheet("background-color: black;")
        
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Display area
        self.display = TeleprompterDisplay()
        self.display.setFont(QFont("Arial", 32))
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(
            """
            QTextEdit {
                background-color: black;
                color: white;
                padding: 40px;
                line-height: 180%;
                border: none;
            }
            QScrollBar:vertical {
                width: 0px;
            }
            """
        )
        layout.addWidget(self.display)
        
        # Control overlay (hidden by default)
        self.control_overlay = QWidget()
        self.control_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); padding: 10px;"
        )
        self.control_overlay.hide()
        
        overlay_layout = QHBoxLayout(self.control_overlay)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶")
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                color: black;
                font-size: 24px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
            """
        )
        self.play_btn.clicked.connect(self.toggle_playback)
        overlay_layout.addWidget(self.play_btn)
        
        # Speed indicator
        self.speed_label = QLabel("Speed: 5")
        self.speed_label.setStyleSheet("color: white; font-size: 18px;")
        overlay_layout.addWidget(self.speed_label)
        
        overlay_layout.addStretch()
        
        # Exit button
        exit_btn = QPushButton("Exit Fullscreen")
        exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #d00;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #a00;
            }
            """
        )
        exit_btn.clicked.connect(self.close)
        overlay_layout.addWidget(exit_btn)
        
        layout.addWidget(self.control_overlay)
        
        # Hide cursor after inactivity
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.hide_cursor)
        self.cursor_timer.start(3000)  # 3 seconds
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Space for play/pause
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_playback)
        # Escape to exit fullscreen
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)
        # Up/Down for speed
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, self.increase_speed)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, self.decrease_speed)
        # R to reset
        QShortcut(QKeySequence("R"), self, self.reset_position)
        # M for mouse toggle
        QShortcut(QKeySequence("M"), self, self.toggle_controls)
        
    def set_content(self, text: str):
        """Set the teleprompter text content."""
        self.display.setPlainText(text)
        self.reset_position()
        
    def set_font(self, font: QFont):
        """Set the display font."""
        self.display.setFont(font)
        
    def set_mirror_mode(self, enabled: bool):
        """Enable or disable mirror mode."""
        self.display.set_mirrored(enabled)
        
    def set_alignment(self, alignment: Qt.AlignmentFlag):
        """Set text alignment."""
        self.display.setAlignment(alignment)
        
    def set_scroll_speed(self, speed: int):
        """Set the scroll speed (1-10)."""
        self.scroll_speed = speed
        self.speed_label.setText(f"Speed: {speed}")
        
    def toggle_playback(self):
        """Toggle play/pause state."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
            
    def play(self):
        """Start scrolling."""
        self.is_playing = True
        self.play_btn.setText("⏸")
        self.scroll_timer.start(50)  # Update every 50ms
        
    def pause(self):
        """Pause scrolling."""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.scroll_timer.stop()
        
    def reset_position(self):
        """Reset scroll position to top."""
        self.display.verticalScrollBar().setValue(0)
        self.pause()
        
    def auto_scroll(self):
        """Automatically scroll the display."""
        if self.is_playing:
            scrollbar = self.display.verticalScrollBar()
            current_value = scrollbar.value()
            max_value = scrollbar.maximum()
            
            if current_value < max_value:
                scrollbar.setValue(current_value + self.scroll_speed)
            else:
                # Reached the end
                self.pause()
                
    def increase_speed(self):
        """Increase scroll speed."""
        if self.scroll_speed < 10:
            self.set_scroll_speed(self.scroll_speed + 1)
            
    def decrease_speed(self):
        """Decrease scroll speed."""
        if self.scroll_speed > 1:
            self.set_scroll_speed(self.scroll_speed - 1)
            
    def toggle_controls(self):
        """Toggle control overlay visibility."""
        if self.control_overlay.isVisible():
            self.control_overlay.hide()
        else:
            self.control_overlay.show()
            self.cursor_timer.start(3000)
            
    def mouseMoveEvent(self, event):
        """Show cursor and controls on mouse movement."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.control_overlay.show()
        self.cursor_timer.start(3000)
        super().mouseMoveEvent(event)
        
    def hide_cursor(self):
        """Hide cursor and controls after inactivity."""
        if self.is_playing:
            self.setCursor(Qt.CursorShape.BlankCursor)
            self.control_overlay.hide()
            
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.showFullScreen()
        
    def closeEvent(self, event):
        """Handle close event."""
        self.pause()
        self.closed.emit()
        super().closeEvent(event)