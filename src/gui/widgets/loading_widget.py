"""Loading and empty state widgets."""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class LoadingSpinner(QWidget):
    """Animated loading spinner widget."""
    
    def __init__(self, size: int = 50, color: QColor = None):
        """Initialize the loading spinner."""
        super().__init__()
        self.size = size
        self.color = color or QColor(100, 100, 100)
        self._angle = 0
        
        self.setFixedSize(size, size)
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)  # Update every 50ms
        self.show()
        
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        """Rotate the spinner."""
        self._angle = (self._angle + 30) % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and radius
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 5
        
        # Draw spinning arc
        pen = QPen(self.color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw arc
        painter.drawArc(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
            self._angle * 16,  # QT uses 16ths of a degree
            270 * 16  # 270 degree arc
        )


class LoadingWidget(QWidget):
    """Widget to show during loading operations."""
    
    def __init__(self, message: str = "Loading..."):
        """Initialize the loading widget."""
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Spinner
        self.spinner = LoadingSpinner()
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Message
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #666; font-size: 14px; margin-top: 10px;")
        layout.addWidget(self.label)
        
    def set_message(self, message: str):
        """Update the loading message."""
        self.label.setText(message)
        
    def start(self):
        """Start the loading animation."""
        self.spinner.start()
        self.show()
        
    def stop(self):
        """Stop the loading animation."""
        self.spinner.stop()
        self.hide()


class EmptyStateWidget(QWidget):
    """Widget to show when there's no content."""
    
    def __init__(self, icon: str = "", title: str = "No Content", 
                 message: str = "", action_text: str = None):
        """Initialize the empty state widget."""
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        # Icon (emoji or symbol)
        if icon:
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px;")
            layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # Message
        if message:
            message_label = QLabel(message)
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("font-size: 14px; color: #666;")
            message_label.setWordWrap(True)
            layout.addWidget(message_label)
            
        # Optional action button
        if action_text:
            from PyQt6.QtWidgets import QPushButton
            self.action_button = QPushButton(action_text)
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #0d6efd;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0b5ed7;
                }
            """)
            layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)