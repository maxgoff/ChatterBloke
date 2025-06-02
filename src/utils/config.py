"""Configuration management for ChatterBloke."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    app_name: str = Field(default="ChatterBloke", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Database Settings
    database_url: str = Field(
        default="sqlite:///data/chatterbloke.db", env="DATABASE_URL"
    )

    # Audio Settings
    audio_sample_rate: int = Field(default=44100, env="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, env="AUDIO_CHANNELS")
    audio_chunk_size: int = Field(default=1024, env="AUDIO_CHUNK_SIZE")
    max_recording_duration: int = Field(default=300, env="MAX_RECORDING_DURATION")
    max_audio_file_size: int = Field(default=104857600, env="MAX_AUDIO_FILE_SIZE")

    # Paths
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    voices_dir: Path = Field(default=Path("data/voices"), env="VOICES_DIR")
    scripts_dir: Path = Field(default=Path("data/scripts"), env="SCRIPTS_DIR")
    outputs_dir: Path = Field(default=Path("data/outputs"), env="OUTPUTS_DIR")
    backups_dir: Path = Field(default=Path("data/backups"), env="BACKUPS_DIR")
    logs_dir: Path = Field(default=Path("data/logs"), env="LOGS_DIR")

    # API Settings
    api_host: str = Field(default="127.0.0.1", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=False, env="API_RELOAD")

    # Ollama Settings
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=30, env="OLLAMA_TIMEOUT")

    # TTS Settings
    tts_default_speed: float = Field(default=1.0, env="TTS_DEFAULT_SPEED")
    tts_default_pitch: float = Field(default=1.0, env="TTS_DEFAULT_PITCH")
    tts_queue_size: int = Field(default=10, env="TTS_QUEUE_SIZE")
    
    # Chatterbox Model Settings
    chatterbox_model_path: Optional[Path] = Field(default=None, env="CHATTERBOX_MODEL_PATH")
    chatterbox_use_local_models: bool = Field(default=False, env="CHATTERBOX_USE_LOCAL_MODELS")

    # UI Settings
    theme: str = Field(default="light", env="THEME")
    font_family: str = Field(default="Arial", env="FONT_FAMILY")
    font_size: int = Field(default=12, env="FONT_SIZE")
    window_width: int = Field(default=1200, env="WINDOW_WIDTH")
    window_height: int = Field(default=800, env="WINDOW_HEIGHT")

    # Backup Settings
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_interval: int = Field(default=86400, env="BACKUP_INTERVAL")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme."""
        valid_themes = ["light", "dark"]
        if v.lower() not in valid_themes:
            raise ValueError(f"Invalid theme: {v}")
        return v.lower()

    @field_validator(
        "data_dir",
        "voices_dir",
        "scripts_dir",
        "outputs_dir",
        "backups_dir",
        "logs_dir",
    )
    @classmethod
    def ensure_paths_exist(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def api_url(self) -> str:
        """Get full API URL."""
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def voices_profiles_dir(self) -> Path:
        """Get voice profiles directory."""
        path = self.voices_dir / "profiles"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def voices_samples_dir(self) -> Path:
        """Get voice samples directory."""
        path = self.voices_dir / "samples"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def temp_dir(self) -> Path:
        """Get temporary directory."""
        path = self.data_dir / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_log_file_path(self) -> Path:
        """Get log file path with date."""
        from datetime import datetime

        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.logs_dir / f"chatterbloke-{date_str}.log"


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings


def reset_settings() -> None:
    """Reset settings instance (useful for testing)."""
    global settings
    settings = None