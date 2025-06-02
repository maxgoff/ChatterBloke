"""LLM integration API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from src.api.models import (
    LLMGenerateRequest,
    LLMImproveRequest,
    LLMResponse,
    ModelListResponse,
)
from src.services.ollama_service import get_ollama_service
from src.utils.config import get_settings


router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/generate", response_model=LLMResponse)
async def generate_script_content(
    request: LLMGenerateRequest,
) -> LLMResponse:
    """Generate script content using LLM."""
    logger.info(f"LLM generate request: {request.prompt[:50]}...")
    
    try:
        ollama = get_ollama_service()
        result = await ollama.generate_script(
            prompt=request.prompt,
            script_type=request.script_type or "general",
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return LLMResponse(
            success=True,
            result=result,
            model=request.model or settings.ollama_model,
            tokens_used=len(result.split()),  # Approximate token count
        )
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve", response_model=LLMResponse)
async def improve_existing_script(
    request: LLMImproveRequest,
) -> LLMResponse:
    """Improve an existing script using LLM."""
    logger.info(f"LLM improve request for script of length: {len(request.script)}")
    
    try:
        ollama = get_ollama_service()
        result = await ollama.improve_script(
            script=request.script,
            instructions=request.instructions,
            model=request.model,
            temperature=request.temperature,
        )
        
        return LLMResponse(
            success=True,
            result=result,
            model=request.model or settings.ollama_model,
            tokens_used=len(result.split()),  # Approximate token count
        )
    except Exception as e:
        logger.error(f"Failed to improve script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelListResponse)
async def list_available_models() -> ModelListResponse:
    """List available LLM models."""
    try:
        ollama = get_ollama_service()
        models = await ollama.list_models()
        
        return ModelListResponse(
            success=True,
            models=models,
        )
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        # Return default models on error
        return ModelListResponse(
            success=True,
            models=[settings.ollama_model, "llama2", "mistral", "codellama"],
        )


@router.post("/check-grammar")
async def check_grammar(text: str, model: Optional[str] = None) -> dict:
    """Check grammar and get corrections."""
    logger.info(f"Grammar check request for text of length: {len(text)}")
    
    try:
        ollama = get_ollama_service()
        result = await ollama.check_grammar(text=text, model=model)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to check grammar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_suggestions(
    script: str,
    focus_areas: Optional[List[str]] = None,
    model: Optional[str] = None
) -> dict:
    """Get improvement suggestions for a script."""
    logger.info(f"Suggestion request for script of length: {len(script)}")
    
    try:
        ollama = get_ollama_service()
        suggestions = await ollama.suggest_improvements(
            script=script,
            focus_areas=focus_areas,
            model=model
        )
        
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))