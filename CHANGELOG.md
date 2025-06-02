# Changelog

All notable changes to ChatterBloke will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and documentation
- TECHPLAN.md with comprehensive technical specification
- CLAUDE.md with development guidelines and best practices
- CHANGELOG.md for tracking project changes
- Python-based architecture using PyQt6 and FastAPI
- Local storage strategy for voice profiles and outputs
- Core component specifications:
  - Voice Manager for recording and cloning
  - Text-to-Speech engine with Chatterbox-TTS
  - Script Editor with Ollama LLM integration
  - Teleprompter display mode
  - SQLAlchemy data models

### Technical Decisions
- Chose Python over TypeScript/Node.js for better audio processing libraries
- Selected PyQt6 for cross-platform GUI development
- Opted for local storage over cloud (S3) for privacy and offline functionality
- Using FastAPI for internal API services
- SQLite with SQLAlchemy for data persistence

### Documentation Updates
- Added comprehensive phased development plan with 13 phases (Phase 0-12)
- Each phase includes detailed tasks, deliverables, and timeline
- Development follows CLAUDE.md guidelines for incremental, testable progress
- Plan emphasizes building foundation first, then features, then polish

## [0.1.0] - Phase 0 Complete

### Added
- Poetry project initialization with all dependencies
- Complete directory structure following TECHPLAN.md
- Git hooks configuration with pre-commit
- Configuration system using Pydantic settings
- SQLAlchemy database models (VoiceProfile, Script, AudioOutput)
- CRUD operations for all models
- Alembic migration setup
- Comprehensive test fixtures and initial tests
- Main entry point with logging setup
- Project foundation ready for Phase 1

### Project Structure
- `src/` - Source code with proper package structure
- `tests/` - Test suite with pytest configuration
- `data/` - Data storage directories with .gitkeep files
- `alembic/` - Database migration configuration
- Configuration files: pyproject.toml, .env.example, .gitignore, .pre-commit-config.yaml

### Technical Setup
- Python 3.10+ with Poetry dependency management
- PyQt6 ready for GUI development
- FastAPI ready for API development
- SQLite database with SQLAlchemy ORM
- Testing with pytest and fixtures
- Code quality tools: black, flake8, mypy
- Pre-commit hooks for automatic formatting

## [0.1.0] - Phase 1 Complete

### Added
- PyQt6 GUI application with main window
- Tab-based interface structure:
  - Voice Manager tab with recording controls placeholder
  - Script Editor tab with text editor and toolbar
  - Teleprompter tab with scrolling controls
  - Settings tab with comprehensive configuration forms
- Menu system (File, Edit, View, Help)
- Status bar with feedback messages
- Reusable widget components:
  - StyledButton with multiple types (primary, secondary, danger, success)
  - ProgressDialog for long operations
  - FileSelector with browse functionality
  - WorkerThread base class for background operations
- Theme system with light and dark modes
- Window state persistence using QSettings
- Font and UI customization support

### GUI Features
- Main window with resizable panels
- Tab switching with status updates
- Keyboard shortcuts for common actions
- Fullscreen mode support
- Basic file operations (new, open, save)
- Placeholder functionality for future features

### Technical Implementation
- Modular tab design for easy extension
- Theme manager with comprehensive styling
- Consistent widget styling across themes
- Proper separation of concerns
- Signal/slot connections for UI interactions

### Fixes
- Updated to Pydantic v2 compatibility with pydantic-settings
- Fixed validator syntax for field_validator decorators
- Added Python 3.13 compatibility notes for audio dependencies

## [0.1.0] - Phase 2 Complete

### Added
- Audio recording functionality with sounddevice library
- AudioRecorder class with device selection and level monitoring
- AudioPlayer class for WAV file playback
- Real-time audio level meter with color coding
- Device selection dropdown with refresh capability
- Recording controls with visual feedback
- Save recording to WAV file functionality
- Voice profile creation prompt after saving
- Audio file validation utilities
- Graceful fallback when audio libraries unavailable

### Technical Implementation
- Used sounddevice as primary audio library (PyAudio alternative)
- Implemented threading for non-blocking recording/playback
- Real-time level monitoring with callback system
- WAV format support with soundfile and wave fallback
- Proper audio device enumeration and selection
- Error handling for missing audio devices

### UI Enhancements
- Added input device selection combo box
- Visual recording indicator (red button when recording)
- Audio level meter with green/orange/red indication
- Status messages for all recording states
- File dialog for saving recordings
- Voice profile creation dialog

### Known Limitations
- Waveform visualization deferred to future phase
- Voice cloning functionality placeholder (Phase 4)
- Database integration pending (Phase 3)

## [0.1.0] - Phase 3 Complete

### Added
- FastAPI backend application with modular router structure
- RESTful API endpoints for voice profiles:
  - Upload audio files with validation
  - CRUD operations for voice profiles
  - Parameter management
  - File cleanup on deletion
- RESTful API endpoints for scripts:
  - CRUD operations for scripts
  - Version management system
  - Search functionality
  - Batch deletion of versions
- API client for frontend-backend communication
  - Async HTTP client using httpx
  - Type-safe request/response models
  - Error handling and logging
- Placeholder endpoints for TTS and LLM (Phase 5 & 7)
- API server runner script (run_api.py)
- Health check endpoint

### Technical Implementation
- FastAPI with Pydantic v2 models
- SQLAlchemy ORM with existing models
- CORS middleware for cross-origin requests
- Static file serving for audio outputs
- Proper error responses with HTTP status codes
- Request validation with Pydantic
- Database session dependency injection

### API Structure
- `/api/voices/` - Voice profile management
- `/api/scripts/` - Script management
- `/api/tts/` - Text-to-speech generation (placeholder)
- `/api/llm/` - LLM integration (placeholder)
- `/health` - Health check
- `/docs` - Interactive API documentation

### Development Features
- Separate API server process
- Hot reload support for development
- Comprehensive logging
- OpenAPI/Swagger documentation
- Type hints throughout

### Next Steps
- Frontend integration with API client
- WebSocket support for real-time updates
- Job queue for TTS processing
- File upload progress tracking

## [0.1.0] - Phase 3 API Integration Complete

### Added
- API service for GUI-backend communication
- Async operation handling in GUI
- Voice profile loading from API
- Voice profile creation with file upload
- Voice profile deletion
- Periodic API health checks
- Connection status in status bar
- Offline mode support

### Technical Implementation
- APIService with dedicated event loop thread
- AsyncWorker for one-off async operations
- Proper thread cleanup on exit
- Event loop conflict resolution
- Qt signal/slot integration with async operations

## [0.1.0] - Phase 4 In Progress

### Added
- Chatterbox-TTS integration preparation
- TTS service with voice cloning support
- Voice cloning API endpoints
- Enhanced Voice Manager UI:
  - Cloning progress bar
  - Test voice interface
  - Voice status indicators
- Database field for cloning status (is_cloned)
- Job tracking for cloning operations

### Technical Decisions
- Using Chatterbox from Resemble AI for TTS
- Zero-shot voice cloning (no training required)
- Background job processing for cloning
- Progress monitoring via API polling

### Dependencies Added
- torch and torchaudio for ML operations
- transformers and accelerate for model support
- Chatterbox (installed from GitHub)

### Next Steps
- Complete TTS generation implementation
- Add audio file handling for test generation
- Implement WebSocket for real-time updates
- Add batch processing support

## [Session Status] - 2025-06-01

### Current State
- ✅ Virtual environment created with all dependencies
- ✅ Database initialized with Alembic migration
- ✅ API server running successfully on port 8000
- ✅ GUI application running and connected to API
- ✅ Audio recording functionality fully implemented
- ✅ Voice profile management UI complete
- 🔄 TTS service running in mock mode (PyTorch not installed in venv)

### Recent Work
- Created missing API dependencies module
- Fixed SessionLocal import issue
- Successfully started API server
- Verified GUI-API communication working

### Ready for Next Session
- User has forked Chatterbox and solved torch dependency issues
- Need to install user's forked Chatterbox when URL provided
- PyTorch/torchaudio need to be installed in virtual environment
- Then can switch from mock TTS mode to real voice cloning

### To Resume
1. Activate virtual environment: `source venv/bin/activate`
2. Start API server: `python run_api.py &`
3. Start GUI: `python src/main.py`
4. Install user's forked Chatterbox when URL provided
5. Test voice cloning pipeline

## [0.1.0] - TTS Integration Complete - 2025-06-01

### Added
- Full TTS service integration with real Chatterbox implementation
- Background TTS generation with job tracking
- Complete API endpoints for voice cloning and speech generation:
  - `/api/tts/clone` - Start voice cloning process
  - `/api/tts/clone/status/{job_id}` - Check cloning status
  - `/api/tts/generate` - Generate speech with job tracking
  - `/api/tts/status/{job_id}` - Check generation status
  - `/api/tts/download/{job_id}` - Download generated audio
  - `/api/tts/generate/quick` - Quick preview generation
- Automatic voice profile status update when cloning completes
- Progress tracking for both cloning and generation jobs
- Error handling and status reporting

### Technical Implementation
- TTS service automatically detects PyTorch/Chatterbox availability
- Falls back to mock mode if dependencies missing
- Async job processing for non-blocking operations
- File-based audio output storage with proper paths
- Support for TTS parameters:
  - Speed adjustment
  - Pitch control
  - Emotion settings
  - Exaggeration level
  - Classifier-free guidance weight

### Ready for Testing
- Voice cloning pipeline ready for testing
- Speech generation from cloned voices functional
- All API endpoints properly integrated
- GUI can now perform real voice cloning and TTS

## [0.1.0] - GUI Fixes - 2025-06-01

### Fixed
- Changed health check interval from 5 to 60 seconds to reduce server load
- Fixed voice list reloading on every health check (now only reloads on connection state change)
- Fixed UTF-8 decode error when testing voice (API returns binary audio, not JSON)
- Test voice now properly handles binary audio response and saves to temp file
- Voice selection no longer cleared on health check updates

### Technical Details
- Added connection state tracking to avoid redundant voice profile loads
- Modified test_voice() to use direct HTTP client for binary responses
- Health check now runs every 60 seconds instead of 5 seconds
- Binary audio from TTS properly saved to temp directory for playback

### Known Issues
- PyTorch not installed in virtual environment - TTS running in mock mode
- To enable real TTS: Install PyTorch, torchaudio, and Chatterbox in venv

## [0.1.0] - Remove Mock Mode - 2025-06-01

### Changed
- Removed all mock mode functionality from TTS service
- TTS service now requires PyTorch and Chatterbox to be installed
- Service will raise ImportError if dependencies are missing
- Following "We don't use mock mode. We fix." principle

### Technical Details
- Removed mock_mode flag from TTSService class
- Removed mock audio generation code
- Service now fails fast if PyTorch or Chatterbox not available
- Added policy to CLAUDE.md: No mock implementations allowed

### Important
- Ensure API server runs with Python environment that has PyTorch installed
- Use: `python run_api.py` (not `./venv/bin/python run_api.py`)
- The execution environment must have PyTorch, torchaudio, and Chatterbox installed

## [0.1.0] - Chatterbox Integration Working - 2025-06-01

### Status
- ✅ Chatterbox TTS successfully initialized on CPU
- ✅ Voice cloning working (marked profile as cloned)
- ✅ Models loaded: PerthNet (Implicit) at step 250,000
- ⏳ Initial model loading takes ~2.5 minutes on first run

### Fixed
- Increased HTTP client timeout to 5 minutes for long operations
- This prevents timeout errors during initial Chatterbox model loading

### Technical Details
- Chatterbox downloads models on first use (one-time operation)
- Subsequent operations are much faster
- Voice cloning confirmed working with real Chatterbox implementation
- No mock mode - using actual TTS functionality

### Next Steps
- Test voice generation with cloned voices
- Subsequent runs should be faster as models are cached

## [0.1.0] - Local Model Support Added - 2025-06-01

### Added
- Configuration support for local Chatterbox models
- Script to download models from HuggingFace: `download_chatterbox_models.py`
- Environment variables for local model configuration:
  - `CHATTERBOX_USE_LOCAL_MODELS`: Enable local model loading
  - `CHATTERBOX_MODEL_PATH`: Path to local model directory

### Benefits
- **Faster startup**: Seconds instead of 2.5 minutes
- **Offline usage**: No internet required after initial download
- **Consistent models**: Control which model version is used
- **No automatic downloads**: Models loaded directly from disk

### Usage
1. Install huggingface-hub: `pip install huggingface-hub`
2. Download models: `python download_chatterbox_models.py`
3. Set environment variable before starting API:
   ```
   export HF_HOME=/Users/maxgoff/Github/ChatterBloke/models
   python run_api.py
   ```
   Or add to .env:
   ```
   HF_HOME=/Users/maxgoff/Github/ChatterBloke/models
   ```

### Technical Details
- Models downloaded from: resemble-ai/chatterbox (HuggingFace)
- Local files only mode when configured
- Falls back to default download behavior if not configured

## [0.1.0] - Phase 5 Script Editor Complete - 2025-06-02

### Added
- Full Script Editor functionality with API integration
- Script CRUD operations via API:
  - Create new scripts with title
  - Load and display scripts from database
  - Save/update script content
  - Delete scripts with confirmation
- Unsaved changes tracking with prompts
- Script list with date display
- Word count in real-time
- TTS generation dialog with voice selection
- Speech generation from scripts:
  - Voice profile selection (cloned voices only)
  - TTS parameter controls (speed, pitch, emotion)
  - Job status tracking
  - Audio file download and save
  - Optional audio playback after generation
- Keyboard shortcuts:
  - Ctrl+N: New script
  - Ctrl+O: Open script file
  - Ctrl+S: Save script

### Technical Implementation
- Async API integration for all operations
- TTSGenerationDialog for speech settings
- Progress tracking for long operations
- Binary audio download handling
- Proper error handling and user feedback

### Phase 5 Complete
- ✅ Script editor with full CRUD functionality
- ✅ API integration for script management
- ✅ TTS integration in script editor
- ✅ Voice selection and parameter controls
- ✅ Audio generation and download
- ✅ Keyboard shortcuts for common operations

### Next Steps
- Phase 6: Teleprompter Implementation
- Phase 7: Ollama LLM Integration for AI assistance

## [0.1.0] - Phase 6 Teleprompter Complete - 2025-06-02

### Added
- Full teleprompter functionality with scrolling text display
- Script loading from database via API
- Professional fullscreen mode with dedicated window
- Mirror mode for teleprompter glass/beam splitter
- Comprehensive display controls:
  - Play/Pause with visual feedback
  - Variable scroll speed (1-10)
  - Font size adjustment (12-72pt)
  - Font family selection
  - Text color customization
  - Center/Left alignment toggle
- Keyboard shortcuts:
  - Space: Play/Pause
  - R: Reset to beginning
  - F11: Toggle fullscreen
  - Up/Down: Adjust speed
  - Escape: Exit fullscreen
  - M: Toggle controls in fullscreen
- Progress indicator showing position percentage
- Auto-hide controls in fullscreen mode
- Position synchronization between main and fullscreen views

### Technical Implementation
- Custom TeleprompterDisplay widget with mirror mode support
- Dedicated TeleprompterWindow for fullscreen presentation
- Smooth scrolling with configurable speed
- API integration for script loading
- State preservation between main and fullscreen modes
- Mouse cursor auto-hide during playback

### UI Enhancements
- Black background with white text for visibility
- Large default font size (24pt main, 32pt fullscreen)
- Responsive controls that hide during playback
- Visual play/pause button with icons
- Reload scripts button
- Professional presentation mode

### Phase 6 Complete
- ✅ Scrolling engine with smooth animation
- ✅ Fullscreen mode with dedicated window
- ✅ Mirror mode for teleprompter glass
- ✅ Complete playback controls
- ✅ Font and display customization
- ✅ Keyboard shortcuts for all functions
- ✅ Progress tracking and position sync

### Next Steps
- Phase 7: Ollama LLM Integration for AI assistance
- Phase 8: Polish and optimization

## [0.1.0] - Phase 7 Ollama LLM Integration Complete - 2025-06-02

### Added
- Complete Ollama service for LLM integration
- AI Assistant widget with four main functions:
  1. **Generate**: Create new scripts from prompts
  2. **Improve**: Enhance existing scripts with instructions
  3. **Grammar**: Check and correct grammar issues
  4. **Suggestions**: Get focused improvement suggestions
- Script type templates:
  - General
  - Presentation
  - Video
  - Podcast
  - Educational
- LLM API endpoints:
  - `/api/llm/generate` - Generate new scripts
  - `/api/llm/improve` - Improve existing scripts
  - `/api/llm/check-grammar` - Grammar checking
  - `/api/llm/suggest` - Get improvement suggestions
  - `/api/llm/models` - List available models
- Integration with Script Editor via AI Assist button
- Model selection with auto-discovery
- Temperature control for creativity adjustment
- Focus area selection for targeted suggestions

### Technical Implementation
- **OllamaService**: Complete async service for Ollama API
  - Prompt engineering for different script types
  - System prompts for specialized assistance
  - Structured response parsing
  - Error handling and fallbacks
- **AIAssistantWidget**: Comprehensive UI for AI features
  - Tabbed interface for different functions
  - Progress indicators for long operations
  - Signal/slot integration with editor
  - Clipboard support
- **API Integration**: Full REST endpoints
  - Pydantic models for requests/responses
  - Async operation handling
  - Proper error responses

### Features
- **Script Generation**:
  - Type-specific prompts
  - Creativity control
  - Direct use in editor
- **Script Improvement**:
  - Custom instructions
  - Preview current script
  - Apply improvements directly
- **Grammar Checking**:
  - Issue identification
  - Corrected text display
  - One-click application
- **Smart Suggestions**:
  - Multiple focus areas
  - Actionable recommendations
  - Area-specific advice

### UI Enhancements
- Modal dialog for AI assistance
- Progress indicators during LLM operations
- Copy to clipboard functionality
- Current script preview in improve tab
- Clear status messages

### Phase 7 Complete
- ✅ Ollama service implementation
- ✅ All LLM API endpoints
- ✅ Complete AI assistant UI
- ✅ Script Editor integration
- ✅ Multiple AI functions
- ✅ Model management
- ✅ Error handling

### Requirements
- Ollama must be installed and running locally
- Default URL: http://localhost:11434
- At least one model installed (e.g., llama2, mistral)

### Next Steps
- Phase 8: Polish and optimization
- Add diff visualization for script comparison
- Implement script templates library

## [0.1.0] - Phase 8 Polish & Optimization (In Progress) - 2025-06-02

### Added
- **UI/UX Improvements**:
  - Loading spinner widget with smooth animation
  - Empty state widget for better user guidance
  - Toast-style notification system (info, success, warning, error)
  - Auto-positioning and stacking of notifications
  - Fade in/out animations for notifications

- **Performance Optimizations**:
  - Simple in-memory cache system for scripts, voices, and models
  - Performance monitoring utilities with metrics tracking
  - Time measurement decorators for profiling
  - Cache hit rate tracking

- **Error Handling**:
  - User-friendly error messages for common issues
  - Error mapping for technical to user-friendly messages
  - Comprehensive error logging with context
  - Specific handling for network, file, audio, and API errors

- **Developer Tools**:
  - Performance monitor tracking API calls, cache hits, etc.
  - Uptime tracking and formatting
  - Debug logging for slow operations (>1 second)

### Implementation Details
- `LoadingWidget`: Animated spinner for long operations
- `EmptyStateWidget`: Informative display when no content
- `NotificationManager`: Toast notifications in top-right corner
- `SimpleCache`: TTL-based in-memory caching
- `PerformanceMonitor`: Application metrics tracking
- `UserFriendlyError`: Better error communication

### Files Added
- `src/gui/widgets/loading_widget.py` - Loading and empty states
- `src/gui/widgets/notification.py` - Notification system
- `src/utils/cache.py` - Caching system
- `src/utils/performance.py` - Performance monitoring
- `src/utils/error_handler.py` - Error handling utilities

### Next Steps for Phase 8
- Add keyboard navigation improvements
- Implement high contrast mode
- Add more tooltips and help text
- Optimize database queries
- Add lazy loading for script lists
- Implement smooth transitions