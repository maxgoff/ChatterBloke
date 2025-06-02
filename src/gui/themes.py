"""Theme management for ChatterBloke GUI."""

from typing import Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QWidget

from src.utils.config import get_settings


class ThemeManager(QObject):
    """Manages application themes and styling."""
    
    themeChanged = pyqtSignal(str)  # Emitted when theme changes
    
    def __init__(self) -> None:
        """Initialize theme manager."""
        super().__init__()
        self.settings = get_settings()
        self.current_theme = self.settings.theme
        self._themes = self._define_themes()
        
    def _define_themes(self) -> Dict[str, Dict[str, str]]:
        """Define available themes."""
        return {
            "light": {
                "name": "Light",
                "stylesheet": """
                QMainWindow {
                    background-color: #f5f5f5;
                }
                
                QTabWidget::pane {
                    background-color: white;
                    border: 1px solid #ddd;
                }
                
                QTabBar::tab {
                    background-color: #e0e0e0;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 2px solid #0066cc;
                }
                
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                
                QListWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                
                QListWidget::item {
                    padding: 4px;
                }
                
                QListWidget::item:selected {
                    background-color: #0066cc;
                    color: white;
                }
                
                QTextEdit {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                
                QLineEdit {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QComboBox {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QSpinBox {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                
                QStatusBar {
                    background-color: #f0f0f0;
                    border-top: 1px solid #ddd;
                }
                
                QMenuBar {
                    background-color: #f8f8f8;
                    border-bottom: 1px solid #ddd;
                }
                
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                
                QMenu {
                    background-color: white;
                    border: 1px solid #ddd;
                }
                
                QMenu::item:selected {
                    background-color: #0066cc;
                    color: white;
                }
                
                QToolBar {
                    background-color: #f8f8f8;
                    border-bottom: 1px solid #ddd;
                    spacing: 3px;
                    padding: 3px;
                }
                
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    text-align: center;
                }
                
                QProgressBar::chunk {
                    background-color: #0066cc;
                    border-radius: 3px;
                }
                """,
            },
            "dark": {
                "name": "Dark",
                "stylesheet": """
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                
                QTabWidget::pane {
                    background-color: #2d2d2d;
                    border: 1px solid #444;
                }
                
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #e0e0e0;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                
                QTabBar::tab:selected {
                    background-color: #2d2d2d;
                    border-bottom: 2px solid #0099ff;
                }
                
                QGroupBox {
                    color: #e0e0e0;
                    font-weight: bold;
                    border: 1px solid #444;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                
                QListWidget {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                }
                
                QListWidget::item {
                    padding: 4px;
                }
                
                QListWidget::item:selected {
                    background-color: #0099ff;
                    color: white;
                }
                
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                }
                
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QComboBox::drop-down {
                    border: none;
                }
                
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    selection-background-color: #0099ff;
                }
                
                QSpinBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QPushButton {
                    background-color: #3c3c3c;
                    color: #e0e0e0;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                
                QPushButton:hover {
                    background-color: #484848;
                }
                
                QPushButton:pressed {
                    background-color: #555;
                }
                
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-top: 1px solid #444;
                }
                
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-bottom: 1px solid #444;
                }
                
                QMenuBar::item:selected {
                    background-color: #3c3c3c;
                }
                
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #444;
                }
                
                QMenu::item:selected {
                    background-color: #0099ff;
                    color: white;
                }
                
                QToolBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-bottom: 1px solid #444;
                    spacing: 3px;
                    padding: 3px;
                }
                
                QToolBar QToolButton {
                    color: #e0e0e0;
                }
                
                QProgressBar {
                    border: 1px solid #444;
                    border-radius: 4px;
                    text-align: center;
                    color: #e0e0e0;
                }
                
                QProgressBar::chunk {
                    background-color: #0099ff;
                    border-radius: 3px;
                }
                
                QLabel {
                    color: #e0e0e0;
                }
                
                QCheckBox {
                    color: #e0e0e0;
                }
                
                QSlider::groove:horizontal {
                    background: #444;
                    height: 6px;
                    border-radius: 3px;
                }
                
                QSlider::handle:horizontal {
                    background: #0099ff;
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    border-radius: 8px;
                }
                """,
            }
        }
        
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self._themes.keys())
        
    def apply_theme(self, theme_name: str, app: Optional[QApplication] = None) -> None:
        """Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme to apply
            app: QApplication instance (uses current if not provided)
        """
        if theme_name not in self._themes:
            return
            
        if app is None:
            app = QApplication.instance()
            
        if app is None:
            return
            
        # Apply stylesheet
        theme = self._themes[theme_name]
        app.setStyleSheet(theme["stylesheet"])
        
        # Update current theme
        self.current_theme = theme_name
        
        # Apply font settings
        font = QFont(self.settings.font_family, self.settings.font_size)
        app.setFont(font)
        
        # Emit signal
        self.themeChanged.emit(theme_name)
        
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.
        
        Returns:
            Name of the new theme
        """
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme
        
    def get_theme_stylesheet(self, theme_name: str) -> str:
        """Get stylesheet for a specific theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            Stylesheet string or empty string if theme not found
        """
        theme = self._themes.get(theme_name, {})
        return theme.get("stylesheet", "")
        
    def apply_widget_theme(self, widget: QWidget, theme_name: Optional[str] = None) -> None:
        """Apply theme to a specific widget.
        
        Args:
            widget: Widget to apply theme to
            theme_name: Theme name (uses current if not provided)
        """
        if theme_name is None:
            theme_name = self.current_theme
            
        stylesheet = self.get_theme_stylesheet(theme_name)
        if stylesheet:
            widget.setStyleSheet(stylesheet)


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get or create the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager