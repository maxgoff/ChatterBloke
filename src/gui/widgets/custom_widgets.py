"""Custom reusable widgets for ChatterBloke."""

from typing import Optional, List

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class StyledButton(QPushButton):
    """Custom styled button with consistent appearance."""
    
    def __init__(self, text: str, button_type: str = "default", parent: Optional[QWidget] = None):
        """Initialize styled button.
        
        Args:
            text: Button text
            button_type: Type of button ('primary', 'secondary', 'danger', 'success', 'default')
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.button_type = button_type
        self.apply_style()
        
    def apply_style(self) -> None:
        """Apply styling based on button type."""
        base_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                border: 1px solid;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                opacity: 0.6;
            }
            QPushButton:disabled {
                opacity: 0.4;
            }
        """
        
        styles = {
            "primary": """
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border-color: #0052a3;
                }
                QPushButton:hover {
                    background-color: #0052a3;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border-color: #545b62;
                }
                QPushButton:hover {
                    background-color: #545b62;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border-color: #bd2130;
                }
                QPushButton:hover {
                    background-color: #bd2130;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border-color: #1e7e34;
                }
                QPushButton:hover {
                    background-color: #1e7e34;
                }
            """,
            "default": """
                QPushButton {
                    background-color: #f8f9fa;
                    color: #212529;
                    border-color: #dee2e6;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """,
        }
        
        style = base_style + styles.get(self.button_type, styles["default"])
        self.setStyleSheet(style)
        
    def set_type(self, button_type: str) -> None:
        """Change button type and update styling."""
        self.button_type = button_type
        self.apply_style()


class ProgressDialog(QDialog):
    """Progress dialog for long-running operations."""
    
    def __init__(self, title: str = "Processing", message: str = "Please wait...", 
                 parent: Optional[QWidget] = None):
        """Initialize progress dialog.
        
        Args:
            title: Dialog title
            message: Progress message
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        # Remove close button
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
        # Cancel button
        self.cancel_button = StyledButton("Cancel", "secondary")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def set_message(self, message: str) -> None:
        """Update the progress message."""
        self.message_label.setText(message)
        
    def set_status(self, status: str) -> None:
        """Update the status text."""
        self.status_label.setText(status)
        
    def set_progress(self, value: int) -> None:
        """Set progress value (0-100)."""
        self.progress_bar.setValue(value)
        
    def set_indeterminate(self, indeterminate: bool = True) -> None:
        """Set progress bar to indeterminate mode."""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            
    def set_cancelable(self, cancelable: bool) -> None:
        """Enable or disable cancel button."""
        self.cancel_button.setVisible(cancelable)


class FileSelector(QWidget):
    """File selector widget with browse button."""
    
    fileSelected = pyqtSignal(str)  # Emitted when a file is selected
    
    def __init__(self, 
                 label: str = "File:", 
                 filter: str = "All Files (*.*)",
                 mode: str = "open",
                 parent: Optional[QWidget] = None):
        """Initialize file selector.
        
        Args:
            label: Label text
            filter: File filter for dialog
            mode: 'open' for open file, 'save' for save file, 'directory' for directory
            parent: Parent widget
        """
        super().__init__(parent)
        self.filter = filter
        self.mode = mode
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        if label:
            self.label = QLabel(label)
            layout.addWidget(self.label)
        
        # Path input
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select a file...")
        self.path_edit.textChanged.connect(self.on_path_changed)
        layout.addWidget(self.path_edit)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse)
        layout.addWidget(self.browse_button)
        
    def browse(self) -> None:
        """Open file dialog for selection."""
        if self.mode == "open":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                self.path_edit.text(),
                self.filter
            )
        elif self.mode == "save":
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                self.path_edit.text(),
                self.filter
            )
        elif self.mode == "directory":
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                self.path_edit.text()
            )
        else:
            return
            
        if path:
            self.set_path(path)
            
    def set_path(self, path: str) -> None:
        """Set the file path."""
        self.path_edit.setText(path)
        
    def get_path(self) -> str:
        """Get the current file path."""
        return self.path_edit.text()
        
    def on_path_changed(self, path: str) -> None:
        """Handle path change."""
        self.fileSelected.emit(path)
        
    def set_filter(self, filter: str) -> None:
        """Update file filter."""
        self.filter = filter
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the widget."""
        self.path_edit.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)


class WorkerThread(QThread):
    """Generic worker thread for background operations."""
    
    progress = pyqtSignal(int)  # Progress update (0-100)
    status = pyqtSignal(str)    # Status message
    finished = pyqtSignal(bool) # Finished signal with success flag
    error = pyqtSignal(str)     # Error message
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize worker thread."""
        super().__init__(parent)
        self._is_cancelled = False
        
    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._is_cancelled = True
        
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._is_cancelled
        
    def run(self) -> None:
        """Override this method in subclasses to perform work."""
        # Example implementation
        try:
            for i in range(101):
                if self.is_cancelled():
                    self.finished.emit(False)
                    return
                    
                self.progress.emit(i)
                self.status.emit(f"Processing... {i}%")
                self.msleep(50)  # Simulate work
                
            self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)