"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.models.database import Base, get_db
from src.utils.config import Settings, reset_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        database_url="sqlite:///:memory:",
        data_dir=Path("tests/test_data"),
        voices_dir=Path("tests/test_data/voices"),
        scripts_dir=Path("tests/test_data/scripts"),
        outputs_dir=Path("tests/test_data/outputs"),
        backups_dir=Path("tests/test_data/backups"),
        logs_dir=Path("tests/test_data/logs"),
        debug=True,
    )


@pytest.fixture(scope="session")
def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_engine(
        test_settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    # Begin a nested transaction
    session.begin_nested()
    
    yield session
    
    # Rollback the transaction to clean up test data
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    reset_settings()
    from src.models.database import reset_db
    reset_db()


@pytest.fixture
def mock_audio_file(tmp_path: Path) -> Path:
    """Create a mock audio file."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(b"mock audio data")
    return audio_file


@pytest.fixture
def sample_voice_data() -> dict:
    """Sample voice profile data."""
    return {
        "name": "Test Voice",
        "description": "A test voice profile",
        "audio_file_path": "data/voices/test_voice.wav",
        "model_path": "data/voices/test_voice_model",
        "parameters": {
            "pitch": 1.0,
            "speed": 1.0,
            "emotion": "neutral"
        }
    }


@pytest.fixture
def sample_script_data() -> dict:
    """Sample script data."""
    return {
        "title": "Test Script",
        "content": "This is a test script content.",
        "version": 1
    }


@pytest.fixture
def sample_audio_output_data() -> dict:
    """Sample audio output data."""
    return {
        "script_id": 1,
        "voice_profile_id": 1,
        "file_path": "data/outputs/test_output.wav",
        "parameters": {
            "speed": 1.0,
            "pitch": 1.0
        }
    }