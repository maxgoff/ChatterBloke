"""FastAPI application for ChatterBloke backend."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import llm, script, tts, voice
from src.models import init_db
from src.utils.config import get_settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ChatterBloke API")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down ChatterBloke API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="ChatterBloke API",
        description="Voice cloning and text-to-speech API",
        version=settings.app_version,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(voice.router, prefix="/api/voices", tags=["voices"])
    app.include_router(script.router, prefix="/api/scripts", tags=["scripts"])
    app.include_router(tts.router, prefix="/api/tts", tags=["tts"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    
    # Mount static files for audio outputs
    outputs_dir = settings.outputs_dir
    if outputs_dir.exists():
        app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "ChatterBloke API",
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


# Create the app instance
app = create_app()