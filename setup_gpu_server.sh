#!/bin/bash
# Setup script for ChatterBloke GPU server

echo "ChatterBloke GPU Server Setup"
echo "============================"

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Warning: Not in a conda environment. It's recommended to use conda."
    echo "Create one with: conda create -n chatterbloke python=3.9"
    echo "Then activate with: conda activate chatterbloke"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "1. Installing missing dependencies for TensorFlow..."
pip install absl-py

echo "2. Installing/updating core dependencies..."
pip install --upgrade pip setuptools wheel

echo "3. Fixing protobuf version conflicts..."
# Set environment variable for compatibility
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
# Install compatible protobuf version
pip uninstall -y protobuf
pip install 'protobuf>=3.19.0,<3.20.0'

echo "4. Installing PyTorch with CUDA support..."
# Check CUDA version
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing PyTorch with CUDA..."
    # Install PyTorch with CUDA 11.8 (adjust version as needed)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "No NVIDIA GPU detected. Installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio
fi

echo "4. Installing ChatterBloke requirements..."
pip install -r requirements.txt

echo "5. Installing additional GPU optimization packages..."
pip install nvidia-ml-py3  # For GPU monitoring

echo "6. Setting up database..."
alembic upgrade head

echo "7. Creating necessary directories..."
mkdir -p data/{voices/{samples,profiles},scripts,outputs,logs,temp,backups}

echo "8. Creating .env file if it doesn't exist..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# ChatterBloke GPU Server Configuration

# API Settings
API_HOST=0.0.0.0  # Listen on all interfaces for remote access
API_PORT=8000

# Audio Settings
AUDIO_SAMPLE_RATE=44100
AUDIO_CHANNELS=1
MAX_RECORDING_DURATION=300
MAX_AUDIO_FILE_SIZE=104857600

# Paths
DATA_DIR=data
VOICES_DIR=data/voices
SCRIPTS_DIR=data/scripts
OUTPUTS_DIR=data/outputs
LOGS_DIR=data/logs

# Database
DATABASE_URL=sqlite:///data/chatterbloke.db

# TTS Settings
TTS_DEFAULT_SPEED=1.0
TTS_DEFAULT_PITCH=1.0

# GPU Settings
CUDA_VISIBLE_DEVICES=0  # Adjust based on your GPU setup

# Chatterbox Model Settings
CHATTERBOX_USE_LOCAL_MODELS=false

# Theme (for any local GUI testing)
THEME=dark

# Logging
LOG_LEVEL=INFO
EOF
    echo ".env file created. Please review and adjust settings as needed."
else
    echo ".env file already exists. Skipping..."
fi

echo "9. Testing imports..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if python -c "import torch; torch.cuda.is_available()" 2>/dev/null | grep -q "True"; then
    python -c "import torch; print(f'CUDA device: {torch.cuda.get_device_name(0)}')"
fi

echo "10. Testing Chatterbox import..."
python -c "import chatterbox; print('Chatterbox imported successfully!')" 2>&1

echo ""
echo "Setup complete!"
echo ""
echo "To start the API server:"
echo "  python run_api.py"
echo ""
echo "The server will be accessible at http://YOUR_SERVER_IP:8000"
echo ""
echo "To allow external connections, make sure to:"
echo "1. Configure your firewall to allow port 8000"
echo "2. Use your server's actual IP address in the frontend configuration"
echo ""