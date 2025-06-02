#!/usr/bin/env python
"""Download Chatterbox models from HuggingFace for local use."""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("Please install huggingface_hub: pip install huggingface-hub")
    sys.exit(1)


def download_chatterbox_models(model_id: str = "resemble-ai/chatterbox", local_dir: str = "models/chatterbox"):
    """Download Chatterbox models from HuggingFace.
    
    Args:
        model_id: HuggingFace model repository ID
        local_dir: Local directory to save models
    """
    local_path = Path(local_dir)
    local_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading Chatterbox models from {model_id}...")
    print(f"Saving to: {local_path.absolute()}")
    
    try:
        # Download all model files
        snapshot_download(
            repo_id=model_id,
            local_dir=str(local_path),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print(f"\n✅ Models downloaded successfully to: {local_path.absolute()}")
        print("\nTo use these models, set the following environment variables:")
        print(f"export CHATTERBOX_USE_LOCAL_MODELS=true")
        print(f"export CHATTERBOX_MODEL_PATH={local_path.absolute()}")
        print(f"export HF_HOME={local_path.parent.absolute()}")
        print("\nOr add them to your .env file:")
        print(f"CHATTERBOX_USE_LOCAL_MODELS=true")
        print(f"CHATTERBOX_MODEL_PATH={local_path.absolute()}")
        print(f"HF_HOME={local_path.parent.absolute()}")
        
    except Exception as e:
        print(f"\n❌ Error downloading models: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Chatterbox models for local use")
    parser.add_argument(
        "--model-id",
        default="resemble-ai/chatterbox",
        help="HuggingFace model repository ID (default: resemble-ai/chatterbox)"
    )
    parser.add_argument(
        "--local-dir",
        default="models/chatterbox",
        help="Local directory to save models (default: models/chatterbox)"
    )
    
    args = parser.parse_args()
    download_chatterbox_models(args.model_id, args.local_dir)