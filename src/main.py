"""Main entry point for ChatterBloke application."""

import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parents[1]))

from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.themes import get_theme_manager
from src.models import init_db
from src.utils.config import get_settings


def setup_logging() -> None:
    """Set up logging configuration."""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.get_log_file_path()),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")


def initialize_database() -> None:
    """Initialize database tables."""
    logger = logging.getLogger(__name__)
    logger.info("Initializing database...")
    
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def main() -> None:
    """Main application entry point."""
    # Set up logging
    setup_logging()
    
    # Initialize database
    initialize_database()
    
    logger = logging.getLogger(__name__)
    logger.info("ChatterBloke is ready!")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ChatterBloke")
    app.setOrganizationName("ChatterBloke Team")
    
    # Apply theme
    theme_manager = get_theme_manager()
    theme_manager.apply_theme(get_settings().theme, app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Ensure proper cleanup on exit
    app.aboutToQuit.connect(window.close)
    
    logger.info("GUI launched successfully")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()