"""API client for frontend-backend communication."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from httpx import HTTPStatusError

from src.api.models import (
    ScriptCreate,
    ScriptResponse,
    ScriptUpdate,
    VoiceProfileCreate,
    VoiceProfileResponse,
    VoiceProfileUpdate,
)
from src.utils.config import get_settings


logger = logging.getLogger(__name__)


class APIClient:
    """Client for ChatterBloke API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API (uses settings default if None)
        """
        self.settings = get_settings()
        self.base_url = base_url or self.settings.api_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0, read=300.0),  # 5 minute read timeout for long operations
        )
        
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        
    async def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_detail)
            except:
                pass
            logger.error(f"API error: {e.response.status_code} - {error_detail}")
            raise Exception(f"API error: {error_detail}")
            
    async def _request(
        self, method: str, path: str, **kwargs
    ) -> dict:
        """Make a generic request to the API."""
        response = await self.client.request(method, path, **kwargs)
        return await self._handle_response(response)
            
    # Health check
    async def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            # Use a shorter timeout for health checks to avoid blocking
            response = await self.client.get("/health", timeout=5.0)
            data = await self._handle_response(response)
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
            
    # Voice profile methods
    async def upload_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """Upload an audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Upload response with file details
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "audio/wav")}
            response = await self.client.post("/api/voices/upload", files=files)
            return await self._handle_response(response)
            
    async def create_voice_profile(
        self,
        name: str,
        audio_file_path: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> VoiceProfileResponse:
        """Create a new voice profile."""
        data = VoiceProfileCreate(
            name=name,
            audio_file_path=audio_file_path,
            description=description,
            parameters=parameters or {},
        )
        response = await self.client.post(
            "/api/voices/",
            json=data.model_dump(),
        )
        result = await self._handle_response(response)
        return VoiceProfileResponse(**result)
        
    async def list_voice_profiles(
        self, skip: int = 0, limit: int = 100
    ) -> List[VoiceProfileResponse]:
        """List all voice profiles."""
        response = await self.client.get(
            "/api/voices/",
            params={"skip": skip, "limit": limit},
        )
        result = await self._handle_response(response)
        return [VoiceProfileResponse(**p) for p in result["data"]]
        
    async def get_voice_profile(self, voice_id: int) -> VoiceProfileResponse:
        """Get a specific voice profile."""
        response = await self.client.get(f"/api/voices/{voice_id}")
        result = await self._handle_response(response)
        return VoiceProfileResponse(**result)
        
    async def update_voice_profile(
        self,
        voice_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> VoiceProfileResponse:
        """Update a voice profile."""
        data = VoiceProfileUpdate(
            name=name,
            description=description,
            parameters=parameters,
        )
        response = await self.client.put(
            f"/api/voices/{voice_id}",
            json=data.model_dump(exclude_unset=True),
        )
        result = await self._handle_response(response)
        return VoiceProfileResponse(**result)
        
    async def delete_voice_profile(self, voice_id: int) -> bool:
        """Delete a voice profile."""
        response = await self.client.delete(f"/api/voices/{voice_id}")
        result = await self._handle_response(response)
        return result.get("success", False)
        
    # Script methods
    async def create_script(
        self, title: str, content: str = ""
    ) -> ScriptResponse:
        """Create a new script."""
        data = ScriptCreate(title=title, content=content)
        response = await self.client.post(
            "/api/scripts/",
            json=data.model_dump(),
        )
        result = await self._handle_response(response)
        return ScriptResponse(**result)
        
    async def list_scripts(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[ScriptResponse]:
        """List all scripts."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
            
        response = await self.client.get("/api/scripts/", params=params)
        result = await self._handle_response(response)
        return [ScriptResponse(**s) for s in result["data"]]
        
    async def get_script(self, script_id: int) -> ScriptResponse:
        """Get a specific script."""
        response = await self.client.get(f"/api/scripts/{script_id}")
        result = await self._handle_response(response)
        return ScriptResponse(**result)
        
    async def update_script(
        self,
        script_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ScriptResponse:
        """Update a script."""
        data = ScriptUpdate(title=title, content=content)
        response = await self.client.put(
            f"/api/scripts/{script_id}",
            json=data.model_dump(exclude_unset=True),
        )
        result = await self._handle_response(response)
        return ScriptResponse(**result)
        
    async def delete_script(
        self, script_id: int, delete_versions: bool = False
    ) -> bool:
        """Delete a script."""
        response = await self.client.delete(
            f"/api/scripts/{script_id}",
            params={"delete_versions": delete_versions},
        )
        result = await self._handle_response(response)
        return result.get("success", False)
        
    # TTS methods
    async def generate_speech(
        self,
        text: str,
        voice_id: int,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate speech from text.
        
        Returns:
            Job information including job_id and status
        """
        response = await self.client.post(
            "/api/tts/generate",
            json={
                "text": text,
                "voice_id": voice_id,
                "parameters": parameters or {},
            },
        )
        return await self._handle_response(response)
        
    async def check_tts_status(self, job_id: str) -> Dict[str, Any]:
        """Check TTS job status."""
        response = await self.client.get(f"/api/tts/status/{job_id}")
        return await self._handle_response(response)
        
    async def download_tts_audio(self, job_id: str) -> bytes:
        """Download generated TTS audio."""
        response = await self.client.get(f"/api/tts/download/{job_id}")
        response.raise_for_status()
        return response.content
        
    # LLM methods
    async def generate_script_with_llm(
        self,
        prompt: str,
        script_type: str = "general",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate script content using LLM."""
        response = await self.client.post(
            "/api/llm/generate",
            json={
                "prompt": prompt,
                "script_type": script_type,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        result = await self._handle_response(response)
        return result["result"]
        
    async def improve_script_with_llm(
        self,
        script: str,
        instructions: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Improve script content using LLM."""
        response = await self.client.post(
            "/api/llm/improve",
            json={
                "script": script,
                "instructions": instructions,
                "model": model,
                "temperature": temperature,
            },
        )
        result = await self._handle_response(response)
        return result["result"]
        
    async def list_llm_models(self) -> List[str]:
        """List available LLM models."""
        response = await self.client.get("/api/llm/models")
        result = await self._handle_response(response)
        return result["models"]