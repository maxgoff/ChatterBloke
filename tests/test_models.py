"""Tests for database models."""

import pytest
from sqlalchemy.orm import Session

from src.models import crud
from src.models.database import AudioOutput, Script, VoiceProfile


class TestVoiceProfile:
    """Test VoiceProfile model and CRUD operations."""

    def test_create_voice_profile(self, test_db: Session, sample_voice_data: dict):
        """Test creating a voice profile."""
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        assert voice.id is not None
        assert voice.name == sample_voice_data["name"]
        assert voice.description == sample_voice_data["description"]
        assert voice.parameters == sample_voice_data["parameters"]
        assert voice.created_at is not None
        assert voice.updated_at is not None

    def test_get_voice_profile(self, test_db: Session, sample_voice_data: dict):
        """Test retrieving a voice profile."""
        # Create voice profile
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        # Retrieve by ID
        retrieved = crud.voice_profile.get(db=test_db, id=voice.id)
        assert retrieved is not None
        assert retrieved.id == voice.id
        assert retrieved.name == voice.name

    def test_get_voice_profile_by_name(self, test_db: Session, sample_voice_data: dict):
        """Test retrieving a voice profile by name."""
        # Create voice profile
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        # Retrieve by name
        retrieved = crud.voice_profile.get_by_name(db=test_db, name=voice.name)
        assert retrieved is not None
        assert retrieved.id == voice.id

    def test_update_voice_profile(self, test_db: Session, sample_voice_data: dict):
        """Test updating a voice profile."""
        # Create voice profile
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        # Update
        update_data = {"description": "Updated description"}
        updated = crud.voice_profile.update(db=test_db, db_obj=voice, obj_in=update_data)
        
        assert updated.description == "Updated description"
        assert updated.updated_at > voice.created_at

    def test_update_voice_parameters(self, test_db: Session, sample_voice_data: dict):
        """Test updating voice profile parameters."""
        # Create voice profile
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        # Update parameters
        new_params = {"pitch": 1.5, "emotion": "happy"}
        updated = crud.voice_profile.update_parameters(
            db=test_db, id=voice.id, parameters=new_params
        )
        
        assert updated is not None
        assert updated.parameters["pitch"] == 1.5
        assert updated.parameters["emotion"] == "happy"
        assert updated.parameters["speed"] == 1.0  # Original value preserved

    def test_delete_voice_profile(self, test_db: Session, sample_voice_data: dict):
        """Test deleting a voice profile."""
        # Create voice profile
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        voice_id = voice.id
        
        # Delete
        deleted = crud.voice_profile.delete(db=test_db, id=voice_id)
        assert deleted is not None
        
        # Verify deletion
        retrieved = crud.voice_profile.get(db=test_db, id=voice_id)
        assert retrieved is None

    def test_voice_profile_unique_name(self, test_db: Session, sample_voice_data: dict):
        """Test that voice profile names must be unique."""
        # Create first voice profile
        crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        
        # Try to create another with same name
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)


class TestScript:
    """Test Script model and CRUD operations."""

    def test_create_script(self, test_db: Session, sample_script_data: dict):
        """Test creating a script."""
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        assert script.id is not None
        assert script.title == sample_script_data["title"]
        assert script.content == sample_script_data["content"]
        assert script.version == 1
        assert script.parent_id is None

    def test_get_script_by_title(self, test_db: Session, sample_script_data: dict):
        """Test retrieving a script by title."""
        # Create script
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Retrieve by title
        retrieved = crud.script.get_by_title(db=test_db, title=script.title)
        assert retrieved is not None
        assert retrieved.id == script.id

    def test_create_script_version(self, test_db: Session, sample_script_data: dict):
        """Test creating a new version of a script."""
        # Create original script
        original = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Create new version
        new_content = "This is updated content for version 2"
        version2 = crud.script.create_version(
            db=test_db, script_id=original.id, content=new_content
        )
        
        assert version2 is not None
        assert version2.title == original.title
        assert version2.content == new_content
        assert version2.version == 2
        assert version2.parent_id == original.id

    def test_get_script_versions(self, test_db: Session, sample_script_data: dict):
        """Test retrieving all versions of a script."""
        # Create original and versions
        original = crud.script.create(db=test_db, obj_in=sample_script_data)
        v2 = crud.script.create_version(db=test_db, script_id=original.id, content="v2")
        v3 = crud.script.create_version(db=test_db, script_id=original.id, content="v3")
        
        # Get all versions
        versions = crud.script.get_versions(db=test_db, parent_id=original.id)
        assert len(versions) == 2  # v2 and v3
        assert all(v.parent_id == original.id for v in versions)

    def test_search_scripts(self, test_db: Session):
        """Test searching scripts by title or content."""
        # Create multiple scripts
        scripts_data = [
            {"title": "Python Tutorial", "content": "Learn Python basics"},
            {"title": "JavaScript Guide", "content": "Master JavaScript"},
            {"title": "Data Science", "content": "Python for data analysis"},
        ]
        
        for data in scripts_data:
            crud.script.create(db=test_db, obj_in=data)
        
        # Search by title
        results = crud.script.search(db=test_db, query="Python")
        assert len(results) == 2
        
        # Search by content
        results = crud.script.search(db=test_db, query="JavaScript")
        assert len(results) == 1


class TestAudioOutput:
    """Test AudioOutput model and CRUD operations."""

    def test_create_audio_output(
        self,
        test_db: Session,
        sample_voice_data: dict,
        sample_script_data: dict,
        sample_audio_output_data: dict,
    ):
        """Test creating an audio output."""
        # Create dependencies
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Update IDs in audio output data
        sample_audio_output_data["voice_profile_id"] = voice.id
        sample_audio_output_data["script_id"] = script.id
        
        # Create audio output
        output = crud.audio_output.create(db=test_db, obj_in=sample_audio_output_data)
        
        assert output.id is not None
        assert output.script_id == script.id
        assert output.voice_profile_id == voice.id
        assert output.file_path == sample_audio_output_data["file_path"]
        assert output.parameters == sample_audio_output_data["parameters"]

    def test_get_audio_outputs_by_script(
        self,
        test_db: Session,
        sample_voice_data: dict,
        sample_script_data: dict,
        sample_audio_output_data: dict,
    ):
        """Test retrieving audio outputs by script."""
        # Create dependencies
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Create multiple outputs for the script
        for i in range(3):
            output_data = sample_audio_output_data.copy()
            output_data["voice_profile_id"] = voice.id
            output_data["script_id"] = script.id
            output_data["file_path"] = f"data/outputs/test_output_{i}.wav"
            crud.audio_output.create(db=test_db, obj_in=output_data)
        
        # Get outputs by script
        outputs = crud.audio_output.get_by_script(db=test_db, script_id=script.id)
        assert len(outputs) == 3
        assert all(o.script_id == script.id for o in outputs)

    def test_get_recent_audio_outputs(
        self,
        test_db: Session,
        sample_voice_data: dict,
        sample_script_data: dict,
        sample_audio_output_data: dict,
    ):
        """Test retrieving recent audio outputs."""
        # Create dependencies
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Create multiple outputs
        outputs = []
        for i in range(5):
            output_data = sample_audio_output_data.copy()
            output_data["voice_profile_id"] = voice.id
            output_data["script_id"] = script.id
            output_data["file_path"] = f"data/outputs/test_output_{i}.wav"
            output = crud.audio_output.create(db=test_db, obj_in=output_data)
            outputs.append(output)
        
        # Get recent outputs
        recent = crud.audio_output.get_recent(db=test_db, limit=3)
        assert len(recent) == 3
        # Should be in descending order by creation time
        assert recent[0].id == outputs[-1].id

    def test_cascade_delete(
        self,
        test_db: Session,
        sample_voice_data: dict,
        sample_script_data: dict,
        sample_audio_output_data: dict,
    ):
        """Test that audio outputs are deleted when parent is deleted."""
        # Create dependencies
        voice = crud.voice_profile.create(db=test_db, obj_in=sample_voice_data)
        script = crud.script.create(db=test_db, obj_in=sample_script_data)
        
        # Create audio output
        sample_audio_output_data["voice_profile_id"] = voice.id
        sample_audio_output_data["script_id"] = script.id
        output = crud.audio_output.create(db=test_db, obj_in=sample_audio_output_data)
        output_id = output.id
        
        # Delete voice profile
        crud.voice_profile.delete(db=test_db, id=voice.id)
        
        # Audio output should be deleted
        retrieved = crud.audio_output.get(db=test_db, id=output_id)
        assert retrieved is None