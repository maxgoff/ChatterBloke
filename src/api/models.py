"""Pydantic models for API requests and responses."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base models
class BaseResponse(BaseModel):
    """Base response model."""
    
    success: bool = True
    message: Optional[str] = None


# Voice models
class VoiceProfileBase(BaseModel):
    """Base voice profile model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class VoiceProfileCreate(VoiceProfileBase):
    """Voice profile creation model."""
    
    audio_file_path: str


class VoiceProfileUpdate(BaseModel):
    """Voice profile update model."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    parameters: Optional[Dict[str, Any]] = None


class VoiceProfileResponse(VoiceProfileBase):
    """Voice profile response model."""
    
    id: int
    audio_file_path: Optional[str]
    model_path: Optional[str]
    is_cloned: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class VoiceProfileListResponse(BaseResponse):
    """Voice profile list response."""
    
    data: List[VoiceProfileResponse]
    total: int


# Script models
class ScriptBase(BaseModel):
    """Base script model."""
    
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")


class ScriptCreate(ScriptBase):
    """Script creation model."""
    
    pass


class ScriptUpdate(BaseModel):
    """Script update model."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


class ScriptResponse(ScriptBase):
    """Script response model."""
    
    id: int
    version: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ScriptListResponse(BaseResponse):
    """Script list response."""
    
    data: List[ScriptResponse]
    total: int


# TTS models
class TTSRequest(BaseModel):
    """Text-to-speech request model."""
    
    text: str = Field(..., min_length=1)
    voice_id: int
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TTSJobResponse(BaseResponse):
    """TTS job response model."""
    
    job_id: str
    status: str = "pending"


class TTSStatusResponse(BaseResponse):
    """TTS status response model."""
    
    job_id: str
    status: str
    progress: Optional[int] = None
    result_url: Optional[str] = None
    error: Optional[str] = None


# Audio output models
class AudioOutputResponse(BaseModel):
    """Audio output response model."""
    
    id: int
    script_id: int
    voice_profile_id: int
    file_path: str
    parameters: Dict[str, Any]
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# LLM models
class LLMGenerateRequest(BaseModel):
    """LLM generation request model."""
    
    prompt: str = Field(..., min_length=1)
    script_type: Optional[str] = Field(default="general")
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)


class LLMImproveRequest(BaseModel):
    """LLM improvement request model."""
    
    script: str = Field(..., min_length=1)
    instructions: str = Field(..., min_length=1)
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class LLMResponse(BaseResponse):
    """LLM response model."""
    
    result: str
    model: str
    tokens_used: Optional[int] = None


class ModelListResponse(BaseResponse):
    """Model list response."""
    
    models: List[str]


# File upload models
class FileUploadResponse(BaseResponse):
    """File upload response model."""
    
    filename: str
    file_path: str
    size: int


# Error models
class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = False
    error: str
    detail: Optional[str] = None