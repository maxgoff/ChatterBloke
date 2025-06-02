"""Notification widget for user feedback."""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect


class NotificationWidget(QWidget):
    """Toast-style notification widget."""
    
    closed = pyqtSignal()
    
    def __init__(self, message: str, notification_type: str = "info", 
                 duration: int = 3000, parent=None):
        """Initialize the notification.
        
        Args:
            message: The notification message
            notification_type: Type of notification (info, success, warning, error)
            duration: How long to show the notification in milliseconds (0 = permanent)
            parent: Parent widget
        """
        super().__init__(parent)
        self.duration = duration
        
        # Set up the widget
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(60)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
        # Colors based on type
        colors = {
            "info": ("#0d6efd", "#cfe2ff", "#084298"),
            "success": ("#198754", "#d1e7dd", "#0f5132"),
            "warning": ("#ffc107", "#fff3cd", "#664d03"),
            "error": ("#dc3545", "#f8d7da", "#842029"),
        }
        
        bg_color, light_color, text_color = colors.get(notification_type, colors["info"])
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        icon_label = QLabel(icons.get(notification_type, "ℹ️"))
        icon_label.setStyleSheet(f"font-size: 20px;")
        layout.addWidget(icon_label)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            padding: 0 10px;
        """)
        layout.addWidget(self.message_label, 1)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: none;
                border: none;
                color: {text_color};
                font-size: 20px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }}
        """)
        close_btn.clicked.connect(self.close_notification)
        layout.addWidget(close_btn)
        
        # Set background style
        self.bg_color = bg_color
        self.light_color = light_color
        
        # Opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animations
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.on_fade_out_finished)
        
        # Auto-close timer
        if duration > 0:
            self.close_timer = QTimer()
            self.close_timer.timeout.connect(self.close_notification)
            self.close_timer.setSingleShot(True)
        else:
            self.close_timer = None
            
    def show_notification(self):
        """Show the notification with fade in effect."""
        self.show()
        self.fade_in_animation.start()
        
        if self.close_timer:
            self.close_timer.start(self.duration)
            
    def close_notification(self):
        """Close the notification with fade out effect."""
        if self.close_timer:
            self.close_timer.stop()
        self.fade_out_animation.start()
        
    def on_fade_out_finished(self):
        """Handle fade out completion."""
        self.hide()
        self.closed.emit()
        self.deleteLater()
        
    def paintEvent(self, event):
        """Custom paint for rounded corners and background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.setBrush(QBrush(QColor(self.light_color)))
        painter.setPen(QPen(QColor(self.bg_color), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)


class NotificationManager:
    """Manages notifications for the application."""
    
    _instance = None
    
    def __init__(self, parent_widget):
        """Initialize the notification manager."""
        self.parent_widget = parent_widget
        self.notifications = []
        self.spacing = 10
        NotificationManager._instance = self
        
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of NotificationManager."""
        if cls._instance is None:
            # Return a dummy instance that does nothing if not initialized
            return cls._DummyNotificationManager()
        return cls._instance
    
    class _DummyNotificationManager:
        """Dummy notification manager when real one not available."""
        def show_info(self, *args, **kwargs): pass
        def show_success(self, *args, **kwargs): pass
        def show_warning(self, *args, **kwargs): pass
        def show_error(self, *args, **kwargs): pass
        
    def show_info(self, message: str, duration: int = 3000):
        """Show an info notification."""
        self._show_notification(message, "info", duration)
        
    def show_success(self, message: str, duration: int = 3000):
        """Show a success notification."""
        self._show_notification(message, "success", duration)
        
    def show_warning(self, message: str, duration: int = 4000):
        """Show a warning notification."""
        self._show_notification(message, "warning", duration)
        
    def show_error(self, message: str, duration: int = 5000):
        """Show an error notification."""
        self._show_notification(message, "error", duration)
        
    def _show_notification(self, message: str, notification_type: str, duration: int):
        """Show a notification."""
        notification = NotificationWidget(message, notification_type, duration, self.parent_widget)
        notification.closed.connect(lambda: self._remove_notification(notification))
        
        # Position the notification
        self._position_notification(notification)
        
        # Add to list and show
        self.notifications.append(notification)
        notification.show_notification()
        
    def _position_notification(self, notification: NotificationWidget):
        """Position the notification on screen."""
        if not self.parent_widget:
            return
            
        # Calculate position (top-right corner)
        parent_rect = self.parent_widget.rect()
        x = parent_rect.width() - notification.width() - 20
        
        # Stack notifications
        y = 20
        for existing in self.notifications:
            if existing.isVisible():
                y += existing.height() + self.spacing
                
        notification.move(x, y)
        
    def _remove_notification(self, notification: NotificationWidget):
        """Remove a notification and reposition others."""
        if notification in self.notifications:
            self.notifications.remove(notification)
            self._reposition_all()
            
    def _reposition_all(self):
        """Reposition all visible notifications."""
        if not self.parent_widget:
            return
            
        parent_rect = self.parent_widget.rect()
        y = 20
        
        for notification in self.notifications:
            if notification.isVisible():
                x = parent_rect.width() - notification.width() - 20
                
                # Animate the move
                animation = QPropertyAnimation(notification, b"pos")
                animation.setDuration(200)
                animation.setEndValue(notification.pos())
                animation.setEndValue(QRect(x, y, notification.width(), notification.height()).topLeft())
                animation.start()
                
                y += notification.height() + self.spacing