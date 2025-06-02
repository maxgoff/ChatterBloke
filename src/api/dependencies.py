"""API dependencies for dependency injection."""

from src.models.database import get_db

__all__ = ["get_db"]