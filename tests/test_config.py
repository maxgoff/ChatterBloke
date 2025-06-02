"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from src.utils.config import Settings, get_settings, reset_settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.app_name == "ChatterBloke"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.database_url == "sqlite:///data/chatterbloke.db"

    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        # Set environment variables
        monkeypatch.setenv("APP_NAME", "TestApp")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("API_PORT", "9000")
        
        settings = Settings()
        
        assert settings.app_name == "TestApp"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.api_port == 9000

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log level
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"
        
        # Invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            Settings(log_level="INVALID")

    def test_theme_validation(self):
        """Test theme validation."""
        # Valid themes
        settings = Settings(theme="dark")
        assert settings.theme == "dark"
        
        settings = Settings(theme="LIGHT")
        assert settings.theme == "light"
        
        # Invalid theme
        with pytest.raises(ValueError, match="Invalid theme"):
            Settings(theme="invalid")

    def test_path_creation(self, tmp_path):
        """Test that directories are created automatically."""
        # Use temporary directory for testing
        settings = Settings(
            data_dir=tmp_path / "data",
            voices_dir=tmp_path / "data/voices",
            scripts_dir=tmp_path / "data/scripts",
            outputs_dir=tmp_path / "data/outputs",
            backups_dir=tmp_path / "data/backups",
            logs_dir=tmp_path / "data/logs",
        )
        
        # Check directories were created
        assert settings.data_dir.exists()
        assert settings.voices_dir.exists()
        assert settings.scripts_dir.exists()
        assert settings.outputs_dir.exists()
        assert settings.backups_dir.exists()
        assert settings.logs_dir.exists()

    def test_api_url_property(self):
        """Test API URL property."""
        settings = Settings(api_host="localhost", api_port=8080)
        assert settings.api_url == "http://localhost:8080"

    def test_voices_subdirectories(self, tmp_path):
        """Test voice subdirectory properties."""
        settings = Settings(voices_dir=tmp_path / "voices")
        
        # Access properties to trigger creation
        profiles_dir = settings.voices_profiles_dir
        samples_dir = settings.voices_samples_dir
        
        assert profiles_dir.exists()
        assert samples_dir.exists()
        assert profiles_dir == settings.voices_dir / "profiles"
        assert samples_dir == settings.voices_dir / "samples"

    def test_temp_directory(self, tmp_path):
        """Test temporary directory property."""
        settings = Settings(data_dir=tmp_path / "data")
        
        temp_dir = settings.temp_dir
        assert temp_dir.exists()
        assert temp_dir == settings.data_dir / "temp"

    def test_log_file_path(self):
        """Test log file path generation."""
        from datetime import datetime
        
        settings = Settings()
        log_path = settings.get_log_file_path()
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        expected = settings.logs_dir / f"chatterbloke-{date_str}.log"
        assert log_path == expected


class TestSettingsManagement:
    """Test settings instance management."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_reset_settings(self):
        """Test resetting settings instance."""
        # Get initial instance
        settings1 = get_settings()
        
        # Reset
        reset_settings()
        
        # Get new instance
        settings2 = get_settings()
        
        assert settings1 is not settings2

    def test_settings_from_env_file(self, tmp_path, monkeypatch):
        """Test loading settings from .env file."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "APP_NAME=EnvFileApp\n"
            "DEBUG=true\n"
            "LOG_LEVEL=WARNING\n"
            "API_PORT=7000\n"
        )
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Reset settings to force reload
        reset_settings()
        
        settings = get_settings()
        
        assert settings.app_name == "EnvFileApp"
        assert settings.debug is True
        assert settings.log_level == "WARNING"
        assert settings.api_port == 7000