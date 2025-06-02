# Quick Start Guide for ChatterBloke

## Installation Steps

### Option 1: Using pip with requirements.txt (Recommended for testing)

1. Create a virtual environment:
```bash
cd /Users/maxgoff/Github/ChatterBloke
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Using Poetry (Recommended for development)

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
cd /Users/maxgoff/Github/ChatterBloke
poetry install
```

3. Activate the Poetry shell:
```bash
poetry shell
```

## Running the Application

After installing dependencies with either method:

```bash
python src/main.py
```

## Troubleshooting

### PyAudio Installation Issues

If you encounter issues installing PyAudio on macOS:
```bash
brew install portaudio
pip install pyaudio
```

On Ubuntu/Debian:
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Missing Qt Platform Plugin

If you see "qt.qpa.plugin: Could not find the Qt platform plugin":
- On macOS: Make sure you're not using the system Python
- On Linux: Install `python3-pyqt6` system package

### Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Then edit `.env` with your preferences.

## Quick Test

To verify everything is working:
```bash
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 installed successfully')"
python -c "import sqlalchemy; print('SQLAlchemy installed successfully')"
python -c "from src.main import main; print('ChatterBloke modules loading correctly')"
```

## Development Mode

To run with debug logging:
```bash
DEBUG=true python src/main.py
```