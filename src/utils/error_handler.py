"""User-friendly error handling utilities."""

import logging
import traceback
from typing import Optional, Dict


logger = logging.getLogger(__name__)


class UserFriendlyError(Exception):
    """Exception with user-friendly message."""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None):
        """Initialize with user and technical messages."""
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        super().__init__(self.technical_message)


def get_user_friendly_error(error: Exception) -> str:
    """Convert technical errors to user-friendly messages."""
    error_mappings = {
        # Network errors
        "ConnectionError": "Unable to connect to the server. Please check your internet connection.",
        "TimeoutError": "The operation took too long. Please try again.",
        "HTTPError": "Server error occurred. Please try again later.",
        
        # File errors
        "FileNotFoundError": "The requested file could not be found.",
        "PermissionError": "Permission denied. Please check file permissions.",
        "OSError": "File system error occurred.",
        
        # Audio errors
        "No audio devices found": "No microphone found. Please connect a microphone and try again.",
        "Audio recording failed": "Failed to record audio. Please check your microphone settings.",
        
        # Database errors
        "Database locked": "Database is busy. Please wait a moment and try again.",
        "Integrity constraint": "Data validation error. Please check your input.",
        
        # API errors
        "401": "Authentication failed. Please check your credentials.",
        "403": "Access denied. You don't have permission for this action.",
        "404": "The requested resource was not found.",
        "500": "Server error. Please try again later.",
        "503": "Service temporarily unavailable. Please try again later.",
        
        # Ollama errors
        "Ollama not running": "AI service not available. Please ensure Ollama is running.",
        "Model not found": "AI model not found. Please install the required model.",
        
        # TTS errors
        "PyTorch not available": "Voice cloning service not available. Please install required dependencies.",
        "Voice profile not found": "Voice profile not found. Please create or select a voice.",
    }
    
    error_str = str(error)
    error_type = type(error).__name__
    
    # Check for specific error messages
    for key, message in error_mappings.items():
        if key in error_str or key == error_type:
            return message
            
    # Check for UserFriendlyError
    if isinstance(error, UserFriendlyError):
        return error.user_message
        
    # Default messages by error type
    if "Connection" in error_type:
        return "Connection error. Please check your network settings."
    elif "File" in error_type:
        return "File operation failed. Please check the file path and permissions."
    elif "Permission" in error_type:
        return "Permission denied. Please check your access rights."
    elif "Timeout" in error_type:
        return "Operation timed out. Please try again."
        
    # Generic message
    return "An unexpected error occurred. Please try again or contact support."


def log_error(error: Exception, context: Optional[Dict] = None) -> None:
    """Log error with context for debugging."""
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    if context:
        error_info["context"] = context
        
    logger.error(f"Error occurred: {error_info}")


def handle_error(error: Exception, context: Optional[Dict] = None) -> str:
    """Handle error by logging and returning user-friendly message."""
    log_error(error, context)
    return get_user_friendly_error(error)