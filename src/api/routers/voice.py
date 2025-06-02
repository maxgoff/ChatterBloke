"""Voice management API endpoints."""

import logging
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.models import (
    ErrorResponse,
    FileUploadResponse,
    VoiceProfileCreate,
    VoiceProfileListResponse,
    VoiceProfileResponse,
    VoiceProfileUpdate,
)
from src.models import crud, get_db
from src.utils.audio import validate_audio_file
from src.utils.config import get_settings


router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> FileUploadResponse:
    """Upload an audio file for voice profile creation."""
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".wav", ".mp3", ".flac", ".ogg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported formats: .wav, .mp3, .flac, .ogg"
        )
    
    # Create temporary file
    temp_dir = settings.temp_dir
    temp_path = temp_dir / file.filename
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate audio file
        is_valid, error_msg = validate_audio_file(
            temp_path,
            max_duration=settings.max_recording_duration
        )
        
        if not is_valid:
            temp_path.unlink()  # Delete invalid file
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Move to voices samples directory
        final_path = settings.voices_samples_dir / file.filename
        if final_path.exists():
            # Add timestamp to avoid overwriting
            stem = final_path.stem
            suffix = final_path.suffix
            timestamp = Path(str(temp_path.stat().st_mtime).replace(".", "_"))
            final_path = final_path.parent / f"{stem}_{timestamp}{suffix}"
        
        shutil.move(str(temp_path), str(final_path))
        
        return FileUploadResponse(
            success=True,
            filename=final_path.name,
            file_path=str(final_path),
            size=final_path.stat().st_size,
        )
        
    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=VoiceProfileResponse)
async def create_voice_profile(
    voice_data: VoiceProfileCreate,
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Create a new voice profile."""
    # Check if name already exists
    existing = crud.voice_profile.get_by_name(db, name=voice_data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Voice profile with name '{voice_data.name}' already exists"
        )
    
    # Validate audio file exists
    audio_path = Path(voice_data.audio_file_path)
    if not audio_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Audio file not found: {voice_data.audio_file_path}"
        )
    
    # Create voice profile
    voice_profile = crud.voice_profile.create(
        db,
        obj_in={
            "name": voice_data.name,
            "description": voice_data.description,
            "audio_file_path": voice_data.audio_file_path,
            "parameters": voice_data.parameters,
        }
    )
    
    logger.info(f"Created voice profile: {voice_profile.name} (ID: {voice_profile.id})")
    return voice_profile


@router.get("/", response_model=VoiceProfileListResponse)
async def list_voice_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> VoiceProfileListResponse:
    """List all voice profiles."""
    profiles = crud.voice_profile.get_multi(db, skip=skip, limit=limit)
    total = db.query(crud.voice_profile.model).count()
    
    return VoiceProfileListResponse(
        success=True,
        data=profiles,
        total=total,
    )


@router.get("/{voice_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(
    voice_id: int,
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Get a specific voice profile."""
    voice_profile = crud.voice_profile.get(db, id=voice_id)
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    return voice_profile


@router.put("/{voice_id}", response_model=VoiceProfileResponse)
async def update_voice_profile(
    voice_id: int,
    voice_update: VoiceProfileUpdate,
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Update a voice profile."""
    voice_profile = crud.voice_profile.get(db, id=voice_id)
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    # Check if new name conflicts
    if voice_update.name and voice_update.name != voice_profile.name:
        existing = crud.voice_profile.get_by_name(db, name=voice_update.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Voice profile with name '{voice_update.name}' already exists"
            )
    
    # Update voice profile
    update_data = voice_update.model_dump(exclude_unset=True)
    voice_profile = crud.voice_profile.update(db, db_obj=voice_profile, obj_in=update_data)
    
    logger.info(f"Updated voice profile: {voice_profile.name} (ID: {voice_profile.id})")
    return voice_profile


@router.put("/{voice_id}/parameters", response_model=VoiceProfileResponse)
async def update_voice_parameters(
    voice_id: int,
    parameters: dict,
    db: Session = Depends(get_db),
) -> VoiceProfileResponse:
    """Update voice profile parameters."""
    voice_profile = crud.voice_profile.update_parameters(
        db, id=voice_id, parameters=parameters
    )
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    logger.info(f"Updated parameters for voice profile: {voice_profile.name} (ID: {voice_profile.id})")
    return voice_profile


@router.delete("/{voice_id}")
async def delete_voice_profile(
    voice_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a voice profile."""
    voice_profile = crud.voice_profile.get(db, id=voice_id)
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    # Delete associated files
    if voice_profile.audio_file_path:
        audio_path = Path(voice_profile.audio_file_path)
        if audio_path.exists():
            try:
                audio_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete audio file: {e}")
    
    if voice_profile.model_path:
        model_path = Path(voice_profile.model_path)
        if model_path.exists() and model_path.is_dir():
            try:
                shutil.rmtree(model_path)
            except Exception as e:
                logger.error(f"Failed to delete model directory: {e}")
    
    # Delete from database
    crud.voice_profile.delete(db, id=voice_id)
    
    logger.info(f"Deleted voice profile: {voice_profile.name} (ID: {voice_id})")
    return {"success": True, "message": f"Voice profile '{voice_profile.name}' deleted"}