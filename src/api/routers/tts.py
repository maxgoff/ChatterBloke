"""Text-to-Speech API endpoints."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.models import (
    TTSJobResponse,
    TTSRequest,
    TTSStatusResponse,
)
from src.models import VoiceProfile, crud
from src.services.tts_service import get_tts_service
from src.utils.config import get_settings


router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


# In-memory job tracking (replace with Redis or database in production)
tts_jobs = {}


@router.post("/clone")
async def clone_voice(
    voice_profile_id: int = Form(...),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Start voice cloning process for a voice profile."""
    # Get voice profile
    voice_profile = db.query(VoiceProfile).filter_by(id=voice_profile_id).first()
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
        
    if not voice_profile.audio_file_path:
        raise HTTPException(
            status_code=400,
            detail="Voice profile has no audio file"
        )
        
    # Check if audio file exists
    audio_path = Path(voice_profile.audio_file_path)
    if not audio_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {audio_path}"
        )
        
    # Start cloning process
    tts_service = get_tts_service()
    try:
        job_id = await tts_service.clone_voice(
            voice_profile_id=voice_profile_id,
            audio_path=audio_path
        )
        
        # Update voice profile status
        voice_profile.is_cloned = False  # Will be set to True when complete
        db.commit()
        
        return JSONResponse(
            content={
                "job_id": job_id,
                "message": "Voice cloning started"
            }
        )
    except Exception as e:
        logger.error(f"Failed to start voice cloning: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start voice cloning: {str(e)}"
        )


@router.get("/clone/status/{job_id}")
async def get_clone_status(
    job_id: str,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get status of voice cloning job."""
    tts_service = get_tts_service()
    status = tts_service.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # If cloning completed, update the voice profile
    if status.get("status") == "completed" and status.get("voice_profile_id"):
        voice_profile = db.query(VoiceProfile).filter_by(
            id=status["voice_profile_id"]
        ).first()
        if voice_profile and not voice_profile.is_cloned:
            voice_profile.is_cloned = True
            db.commit()
            logger.info(f"Marked voice profile {voice_profile.id} as cloned")
        
    return JSONResponse(content=status)


async def _process_tts_generation(
    job_id: str,
    tts_request: TTSRequest,
    voice_profile: VoiceProfile,
    tts_service,
    db: Session
) -> None:
    """Process TTS generation in background."""
    try:
        # Update progress
        tts_jobs[job_id]["progress"] = 20
        
        # Get audio prompt path
        audio_prompt_path = None
        if voice_profile.audio_file_path:
            audio_prompt_path = voice_profile.audio_file_path
            
        # Generate speech
        params = tts_request.parameters or {}
        audio_array, sample_rate = await tts_service.generate_speech(
            text=tts_request.text,
            voice_profile_id=voice_profile.id,
            audio_prompt_path=audio_prompt_path,
            speed=params.get("speed", 1.0),
            pitch=params.get("pitch", 1.0),
            emotion=params.get("emotion", "neutral"),
            exaggeration=params.get("exaggeration", 0.5),
            cfg_weight=params.get("cfg_weight", 0.5)
        )
        
        # Update progress
        tts_jobs[job_id]["progress"] = 80
        
        # Save output
        output_path = await tts_service.save_output(
            audio_array=audio_array,
            sample_rate=sample_rate,
            script_id=tts_request.script_id if hasattr(tts_request, 'script_id') else 0,
            voice_profile_id=voice_profile.id,
            format="wav"
        )
        
        # Update job status
        tts_jobs[job_id]["status"] = "completed"
        tts_jobs[job_id]["progress"] = 100
        tts_jobs[job_id]["result_url"] = f"/outputs/{output_path.name}"
        tts_jobs[job_id]["output_path"] = str(output_path)
        
        logger.info(f"TTS generation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"TTS generation failed for job {job_id}: {e}")
        tts_jobs[job_id]["status"] = "failed"
        tts_jobs[job_id]["error"] = str(e)


@router.post("/generate", response_model=TTSJobResponse)
async def generate_speech(
    tts_request: TTSRequest,
    db: Session = Depends(get_db),
) -> TTSJobResponse:
    """Generate speech from text using a voice profile."""
    # Validate voice profile exists
    voice_profile = crud.voice_profile.get(db, id=tts_request.voice_id)
    if not voice_profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job tracking
    tts_jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.utcnow(),
        "text": tts_request.text,
        "voice_id": tts_request.voice_id,
        "parameters": tts_request.parameters,
        "progress": 0,
    }
    
    # Get TTS service and generate speech
    tts_service = get_tts_service()
    
    # Start async generation
    import asyncio
    asyncio.create_task(
        _process_tts_generation(
            job_id, 
            tts_request, 
            voice_profile, 
            tts_service,
            db
        )
    )
    
    logger.info(f"Started TTS job: {job_id} for voice: {voice_profile.name}")
    
    return TTSJobResponse(
        success=True,
        job_id=job_id,
        status="processing",
    )


@router.get("/status/{job_id}", response_model=TTSStatusResponse)
async def get_tts_status(
    job_id: str,
) -> TTSStatusResponse:
    """Check the status of a TTS generation job."""
    if job_id not in tts_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = tts_jobs[job_id]
    
    return TTSStatusResponse(
        success=True,
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        result_url=job.get("result_url"),
        error=job.get("error")
    )


@router.get("/download/{job_id}")
async def download_generated_audio(
    job_id: str,
) -> FileResponse:
    """Download the generated audio file."""
    if job_id not in tts_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = tts_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Get output path
    output_path = job.get("output_path")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename=Path(output_path).name
    )


class QuickTTSRequest(BaseModel):
    """Quick TTS generation request."""
    text: str
    voice_profile_id: Optional[int] = None
    speed: float = 1.0
    pitch: float = 1.0
    emotion: str = "neutral"
    

@router.post("/generate/quick")
async def generate_quick_speech(
    request: QuickTTSRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """Generate speech quickly for preview."""
    # Get voice profile if specified
    audio_prompt_path = None
    if request.voice_profile_id:
        voice_profile = db.query(VoiceProfile).filter_by(id=request.voice_profile_id).first()
        if not voice_profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        if voice_profile.audio_file_path:
            audio_prompt_path = voice_profile.audio_file_path
            
    # Generate speech with provided settings
    tts_service = get_tts_service()
    try:
        audio_array, sample_rate = await tts_service.generate_speech(
            text=request.text,
            voice_profile_id=request.voice_profile_id,
            audio_prompt_path=audio_prompt_path,
            speed=request.speed,
            pitch=request.pitch,
            emotion=request.emotion,
            exaggeration=0.5,
            cfg_weight=0.5
        )
        
        # Return audio data as JSON
        return {
            "audio_data": audio_array.tolist(),
            "sample_rate": sample_rate,
            "duration": len(audio_array) / sample_rate
        }
        
    except Exception as e:
        logger.error(f"Failed to generate quick speech: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech: {str(e)}"
        )