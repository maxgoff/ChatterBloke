"""Teleprompter tab for displaying scrolling scripts."""

import logging
from typing import Optional, Dict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTransform, QPainter, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QColorDialog,
    QFontComboBox,
)

from src.gui.services import get_api_service
from src.gui.widgets.teleprompter_display import TeleprompterDisplay
from src.gui.widgets.teleprompter_window import TeleprompterWindow


class TeleprompterTab(QWidget):
    """Tab for displaying scripts in teleprompter mode."""

    def __init__(self) -> None:
        """Initialize the Teleprompter tab."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.is_playing = False
        self.is_fullscreen = False
        self.scripts_cache: Dict[int, Dict] = {}
        self.current_script_id: Optional[int] = None
        self.fullscreen_window: Optional[TeleprompterWindow] = None
        
        # Scrolling
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.auto_scroll)
        self.scroll_speed = 5  # pixels per update
        
        # API service
        self.api_service = get_api_service()
        self.api_service.connected.connect(self.on_api_connected)
        self.is_connected = False
        
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Control panel at the top
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Display area
        self.display_area = self.create_display_area()
        main_layout.addWidget(self.display_area, 1)  # Take remaining space
        
        # Status bar at the bottom
        self.status_label = QLabel("Ready to display script")
        self.status_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px;"
        )
        main_layout.addWidget(self.status_label)
        
    def create_control_panel(self) -> QGroupBox:
        """Create the control panel with playback controls."""
        control_panel = QGroupBox("Teleprompter Controls")
        layout = QVBoxLayout(control_panel)
        
        # Script selection row
        script_row = QHBoxLayout()
        
        script_row.addWidget(QLabel("Script:"))
        self.script_selector = QComboBox()
        self.script_selector.addItem("(No scripts available)")
        self.script_selector.setMinimumWidth(200)
        self.script_selector.currentIndexChanged.connect(self.on_script_selected)
        script_row.addWidget(self.script_selector)
        
        # Reload scripts button
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setToolTip("Reload scripts")
        self.reload_btn.setMaximumWidth(30)
        self.reload_btn.clicked.connect(self.load_scripts)
        script_row.addWidget(self.reload_btn)
        
        script_row.addStretch()
        
        # Fullscreen button
        self.fullscreen_btn = QPushButton("Fullscreen")
        self.fullscreen_btn.setToolTip("Enter fullscreen mode (F11)")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        script_row.addWidget(self.fullscreen_btn)
        
        layout.addLayout(script_row)
        
        # Playback controls row
        playback_row = QHBoxLayout()
        
        # Play/Pause button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setToolTip("Start/stop scrolling")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setMinimumWidth(100)
        playback_row.addWidget(self.play_btn)
        
        # Reset button
        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setToolTip("Reset to beginning")
        self.reset_btn.clicked.connect(self.reset_position)
        playback_row.addWidget(self.reset_btn)
        
        playback_row.addWidget(QLabel("Speed:"))
        
        # Speed control
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.speed_slider.setMinimumWidth(150)
        playback_row.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("5")
        self.speed_label.setMinimumWidth(20)
        playback_row.addWidget(self.speed_label)
        
        playback_row.addStretch()
        
        # Font size control
        playback_row.addWidget(QLabel("Font Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(12)
        self.font_size_spin.setMaximum(72)
        self.font_size_spin.setValue(24)
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        playback_row.addWidget(self.font_size_spin)
        
        layout.addLayout(playback_row)
        
        # Display options row
        options_row = QHBoxLayout()
        
        # Mirror mode checkbox
        self.mirror_check = QCheckBox("Mirror Mode")
        self.mirror_check.setToolTip("Mirror the display (for teleprompter glass)")
        self.mirror_check.toggled.connect(self.toggle_mirror_mode)
        options_row.addWidget(self.mirror_check)
        
        # Center alignment checkbox
        self.center_check = QCheckBox("Center Text")
        self.center_check.setToolTip("Center align the text")
        self.center_check.setChecked(True)
        self.center_check.toggled.connect(self.toggle_center_alignment)
        options_row.addWidget(self.center_check)
        
        # Font selection
        options_row.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        self.font_combo.setMaximumWidth(150)
        options_row.addWidget(self.font_combo)
        
        # Color selection
        self.color_btn = QPushButton("Text Color")
        self.color_btn.clicked.connect(self.choose_text_color)
        options_row.addWidget(self.color_btn)
        
        options_row.addStretch()
        
        # Progress indicator
        self.progress_label = QLabel("Position: 0%")
        options_row.addWidget(self.progress_label)
        
        layout.addLayout(options_row)
        
        return control_panel
        
    def create_display_area(self) -> TeleprompterDisplay:
        """Create the main display area for the teleprompter."""
        display = TeleprompterDisplay()
        display.setReadOnly(True)
        display.setFont(QFont("Arial", 24))
        display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        display.setStyleSheet(
            """
            QTextEdit {
                background-color: black;
                color: white;
                padding: 20px;
                line-height: 150%;
            }
            """
        )
        display.setPlainText(
            "Welcome to the Teleprompter!\n\n"
            "Select a script from the dropdown above to begin.\n\n"
            "Use the controls to:\n"
            "• Adjust scrolling speed\n"
            "• Change font size\n"
            "• Enable mirror mode\n"
            "• Enter fullscreen mode\n\n"
            "Press Space or click Play to start scrolling."
        )
        
        # Connect scroll position change
        display.verticalScrollBar().valueChanged.connect(self.on_scroll_position_changed)
        
        return display
        
    def on_api_connected(self, is_connected: bool) -> None:
        """Handle API connection status change."""
        if is_connected and not self.is_connected:
            self.is_connected = True
            # Load scripts when newly connected
            QTimer.singleShot(100, self.load_scripts)
        elif not is_connected and self.is_connected:
            self.is_connected = False
            self.script_selector.clear()
            self.script_selector.addItem("(Offline - API not available)")
            
    def setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Space for play/pause
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_playback)
        # R for reset
        QShortcut(QKeySequence("R"), self, self.reset_position)
        # F11 for fullscreen
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self.toggle_fullscreen)
        # Up/Down arrows for speed control
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, self.increase_speed)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, self.decrease_speed)
        
    def showEvent(self, event) -> None:
        """Handle show event - reload scripts when tab becomes visible."""
        super().showEvent(event)
        # Only reload if connected and it's been more than 2 seconds since last load
        if self.is_connected:
            self.load_scripts()
        
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
                    self.status_label.setText("Failed to load scripts")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
        
    def on_scripts_loaded(self, scripts) -> None:
        """Handle loaded scripts."""
        self.script_selector.clear()
        
        if not scripts:
            self.script_selector.addItem("(No scripts available)")
            return
            
        # Cache scripts and populate selector
        self.scripts_cache = {s.id: s for s in scripts}
        for script in scripts:
            self.script_selector.addItem(script.title, script.id)
            
        self.status_label.setText(f"Loaded {len(scripts)} scripts")
    
    def on_script_selected(self, index: int) -> None:
        """Handle script selection."""
        if index < 0:
            return
            
        script_id = self.script_selector.currentData()
        if script_id and script_id in self.scripts_cache:
            self.load_script(script_id)
            
    def toggle_playback(self) -> None:
        """Toggle play/pause state."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
            
    def play(self) -> None:
        """Start scrolling."""
        self.is_playing = True
        self.play_btn.setText("⏸ Pause")
        self.scroll_timer.start(50)  # Update every 50ms
        self.status_label.setText("Playing...")
        self.logger.info("Teleprompter started")
        
    def pause(self) -> None:
        """Pause scrolling."""
        self.is_playing = False
        self.play_btn.setText("▶ Play")
        self.scroll_timer.stop()
        self.status_label.setText("Paused")
        self.logger.info("Teleprompter paused")
        
    def reset_position(self) -> None:
        """Reset scroll position to top."""
        self.display_area.verticalScrollBar().setValue(0)
        self.pause()
        self.status_label.setText("Reset to beginning")
        
    def auto_scroll(self) -> None:
        """Automatically scroll the display."""
        if self.is_playing:
            scrollbar = self.display_area.verticalScrollBar()
            current_value = scrollbar.value()
            max_value = scrollbar.maximum()
            
            if current_value < max_value:
                # Scroll speed based on slider value
                scroll_amount = self.speed_slider.value()
                scrollbar.setValue(current_value + scroll_amount)
            else:
                # Reached the end
                self.pause()
                self.status_label.setText("Reached end of script")
                
    def on_speed_changed(self, value: int) -> None:
        """Handle speed slider change."""
        self.speed_label.setText(str(value))
        self.scroll_speed = value
        # Update fullscreen window if open
        if self.fullscreen_window and self.fullscreen_window.isVisible():
            self.fullscreen_window.set_scroll_speed(value)
        self.logger.debug(f"Speed changed to: {value}")
        
    def on_font_size_changed(self, value: int) -> None:
        """Handle font size change."""
        font = self.display_area.font()
        font.setPointSize(value)
        self.display_area.setFont(font)
        self.logger.debug(f"Font size changed to: {value}")
        
    def on_scroll_position_changed(self, value: int) -> None:
        """Update progress indicator based on scroll position."""
        scrollbar = self.display_area.verticalScrollBar()
        if scrollbar.maximum() > 0:
            progress = int((value / scrollbar.maximum()) * 100)
            self.progress_label.setText(f"Position: {progress}%")
            
    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.fullscreen_window and self.fullscreen_window.isVisible():
            # Exit fullscreen
            self.fullscreen_window.close()
            self.fullscreen_window = None
            self.fullscreen_btn.setText("Fullscreen")
            self.is_fullscreen = False
            # Resume scrolling in main window if was playing
            if self.is_playing:
                self.play()
        else:
            # Enter fullscreen
            self.create_fullscreen_window()
            self.fullscreen_btn.setText("Exit Fullscreen")
            self.is_fullscreen = True
            # Pause main window scrolling
            if self.is_playing:
                self.pause()
                
    def create_fullscreen_window(self) -> None:
        """Create and show fullscreen teleprompter window."""
        self.fullscreen_window = TeleprompterWindow()
        self.fullscreen_window.closed.connect(self.on_fullscreen_closed)
        
        # Copy current settings
        if self.display_area.toPlainText():
            self.fullscreen_window.set_content(self.display_area.toPlainText())
        
        # Copy display settings
        self.fullscreen_window.set_font(self.display_area.font())
        self.fullscreen_window.set_mirror_mode(self.mirror_check.isChecked())
        self.fullscreen_window.set_alignment(
            Qt.AlignmentFlag.AlignCenter if self.center_check.isChecked() 
            else Qt.AlignmentFlag.AlignLeft
        )
        self.fullscreen_window.set_scroll_speed(self.speed_slider.value())
        
        # Copy scroll position
        current_pos = self.display_area.verticalScrollBar().value()
        max_pos = self.display_area.verticalScrollBar().maximum()
        if max_pos > 0:
            # Set proportional position after content is loaded
            QTimer.singleShot(100, lambda: self.set_fullscreen_scroll_position(current_pos, max_pos))
        
        self.fullscreen_window.show()
        
    def set_fullscreen_scroll_position(self, pos: int, max_pos: int) -> None:
        """Set scroll position in fullscreen window proportionally."""
        if self.fullscreen_window:
            fs_scrollbar = self.fullscreen_window.display.verticalScrollBar()
            fs_max = fs_scrollbar.maximum()
            if fs_max > 0 and max_pos > 0:
                proportional_pos = int((pos / max_pos) * fs_max)
                fs_scrollbar.setValue(proportional_pos)
                
    def on_fullscreen_closed(self) -> None:
        """Handle fullscreen window closed."""
        self.fullscreen_btn.setText("Fullscreen")
        self.is_fullscreen = False
        
        # Copy scroll position back
        if self.fullscreen_window:
            fs_scrollbar = self.fullscreen_window.display.verticalScrollBar()
            fs_pos = fs_scrollbar.value()
            fs_max = fs_scrollbar.maximum()
            
            if fs_max > 0:
                scrollbar = self.display_area.verticalScrollBar()
                max_pos = scrollbar.maximum()
                if max_pos > 0:
                    proportional_pos = int((fs_pos / fs_max) * max_pos)
                    scrollbar.setValue(proportional_pos)
                
    def load_script(self, script_id: int) -> None:
        """Load a specific script content."""
        self.logger.info(f"Loading script ID: {script_id}")
        
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
                    self.display_area.setPlainText(script.content or "(Empty script)")
                    self.reset_position()
                    self.status_label.setText(f"Loaded: {script.title}")
                except Exception as e:
                    self.status_label.setText(f"Error: {str(e)}")
            else:
                QTimer.singleShot(50, check_result)
                
        QTimer.singleShot(0, check_result)
    
    def toggle_mirror_mode(self, checked: bool) -> None:
        """Toggle mirror mode for teleprompter glass."""
        self.display_area.set_mirrored(checked)
        if checked:
            self.status_label.setText("Mirror mode enabled")
            self.logger.info("Mirror mode enabled")
        else:
            self.status_label.setText("Mirror mode disabled")
            self.logger.info("Mirror mode disabled")
            
    def toggle_center_alignment(self, checked: bool) -> None:
        """Toggle text center alignment."""
        if checked:
            self.display_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.display_area.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
    def on_font_changed(self, font: QFont) -> None:
        """Handle font family change."""
        current_font = self.display_area.font()
        current_font.setFamily(font.family())
        self.display_area.setFont(current_font)
        
    def choose_text_color(self) -> None:
        """Open color picker for text color."""
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Choose Text Color")
        if color.isValid():
            self.display_area.setStyleSheet(
                f"""
                QTextEdit {{
                    background-color: black;
                    color: {color.name()};
                    padding: 20px;
                    line-height: 150%;
                }}
                """
            )
            
    def increase_speed(self) -> None:
        """Increase scroll speed."""
        current = self.speed_slider.value()
        if current < 10:
            self.speed_slider.setValue(current + 1)
            
    def decrease_speed(self) -> None:
        """Decrease scroll speed."""
        current = self.speed_slider.value()
        if current > 1:
            self.speed_slider.setValue(current - 1)
            
    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts."""
        # Let QShortcut handle the shortcuts
        super().keyPressEvent(event)