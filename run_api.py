#!/usr/bin/env python
"""Run the ChatterBloke API server."""

import logging
import os
import sys
from pathlib import Path

# Fix for protobuf compatibility issues on some systems
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

from src.utils.config import get_settings


def main():
    """Run the API server."""
    settings = get_settings()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting ChatterBloke API on {settings.api_host}:{settings.api_port}")
    
    # Run the server
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()