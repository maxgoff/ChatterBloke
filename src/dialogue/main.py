#!/usr/bin/env python3
"""Main entry point for ChatterBloke Dialogue application."""

import logging
import os
import platform
import signal
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parents[2]))

from PyQt6.QtWidgets import QApplication

from src.dialogue.main_window import DialogueMainWindow
from src.gui.themes import get_theme_manager
from src.models import init_db
from src.utils.config import get_settings


def setup_signal_handlers():
    """Set up signal handlers to prevent crashes on exit."""
    def signal_handler(sig, frame):
        logging.getLogger(__name__).info(f"Received signal {sig}, shutting down gracefully...")
        QApplication.quit()
    
    # Handle termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ignore SIGPIPE on macOS/Linux
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)


def setup_logging() -> None:
    """Set up logging configuration."""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_file = settings.logs_dir / "chatterbloke_dialogue.log"
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting ChatterBloke Dialogue v0.1.0")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")


def main() -> None:
    """Main application entry point."""
    # Set up signal handlers first
    setup_signal_handlers()
    
    # Set up macOS-specific fixes
    if platform.system() == "Darwin":
        # Disable App Nap
        os.environ['PYTHON_DISABLE_APP_NAP'] = '1'
        # Use native rendering
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    # Set up logging
    setup_logging()
    
    # Initialize database (shared with ChatterBloke)
    logger = logging.getLogger(__name__)
    logger.info("Using shared ChatterBloke database")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ChatterBloke Dialogue")
    app.setOrganizationName("ChatterBloke Team")
    app.setQuitOnLastWindowClosed(True)
    
    # Apply theme
    theme_manager = get_theme_manager()
    theme_manager.apply_theme(get_settings().theme, app)
    
    # Create and show main window
    window = DialogueMainWindow()
    window.show()
    
    logger.info("ChatterBloke Dialogue launched successfully")
    
    # Run the application
    exit_code = app.exec()
    
    # Clean up after Qt event loop exits
    logger.info("Application event loop ended")
    
    # Force cleanup of Qt objects
    window.deleteLater()
    app.processEvents()
    app.deleteLater()
    
    # Exit cleanly
    sys.exit(exit_code)


if __name__ == "__main__":
    main()