"""Audio utilities for ChatterBloke."""

import io
import logging
import queue
import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

import numpy as np

# Try to import audio libraries, fallback gracefully
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    sf = None

from src.utils.config import get_settings


@dataclass
class AudioDeviceInfo:
    """Information about an audio device."""
    
    index: int
    name: str
    channels: int
    sample_rate: float
    is_input: bool
    is_default: bool = False


class AudioRecorder:
    """Audio recorder using sounddevice or fallback methods."""
    
    def __init__(self, sample_rate: int = None, channels: int = None, device: Optional[int] = None):
        """Initialize audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz (uses config default if None)
            channels: Number of channels (uses config default if None)
            device: Device index (uses default if None)
        """
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        self.sample_rate = sample_rate or self.settings.audio_sample_rate
        self.channels = channels or self.settings.audio_channels
        self.device = device
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recorded_frames = []
        self.recording_thread: Optional[threading.Thread] = None
        
        # Callback for level monitoring
        self.level_callback: Optional[Callable[[float], None]] = None
        
        if not SOUNDDEVICE_AVAILABLE:
            self.logger.warning("sounddevice not available. Recording functionality limited.")
            
    def get_available_devices(self) -> list[AudioDeviceInfo]:
        """Get list of available audio input devices."""
        devices = []
        
        if SOUNDDEVICE_AVAILABLE and sd is not None:
            try:
                device_list = sd.query_devices()
                default_input = sd.default.device[0]
                
                for idx, device in enumerate(device_list):
                    if device['max_input_channels'] > 0:
                        devices.append(AudioDeviceInfo(
                            index=idx,
                            name=device['name'],
                            channels=device['max_input_channels'],
                            sample_rate=device['default_samplerate'],
                            is_input=True,
                            is_default=(idx == default_input)
                        ))
            except Exception as e:
                self.logger.error(f"Error querying devices: {e}")
        
        return devices
        
    def set_level_callback(self, callback: Optional[Callable[[float], None]]) -> None:
        """Set callback for audio level monitoring.
        
        Args:
            callback: Function that receives RMS level (0.0 to 1.0)
        """
        self.level_callback = callback
        
    def start_recording(self) -> bool:
        """Start recording audio.
        
        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            self.logger.warning("Already recording")
            return False
            
        if not SOUNDDEVICE_AVAILABLE:
            self.logger.error("sounddevice not available")
            return False
            
        try:
            self.recorded_frames = []
            self.audio_queue = queue.Queue()
            self.is_recording = True
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self._record_thread)
            self.recording_thread.start()
            
            self.logger.info(f"Started recording: {self.sample_rate}Hz, {self.channels} channels")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False
            
    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return audio data.
        
        Returns:
            WAV file data as bytes, or None if no recording
        """
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
            
        # Process recorded frames
        if not self.recorded_frames:
            self.logger.warning("No audio data recorded")
            return None
            
        try:
            # Combine all audio frames
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            
            # Convert to WAV format
            wav_buffer = io.BytesIO()
            if SOUNDFILE_AVAILABLE and sf is not None:
                sf.write(wav_buffer, audio_data, self.sample_rate, format='WAV')
            else:
                # Fallback to wave module
                wav_buffer = self._write_wav_fallback(audio_data)
                
            wav_buffer.seek(0)
            wav_data = wav_buffer.read()
            
            self.logger.info(f"Stopped recording: {len(audio_data) / self.sample_rate:.1f} seconds")
            return wav_data
            
        except Exception as e:
            self.logger.error(f"Error processing recording: {e}")
            return None
            
    def _record_thread(self) -> None:
        """Recording thread function."""
        if not SOUNDDEVICE_AVAILABLE or sd is None:
            return
            
        try:
            def audio_callback(indata, frames, time, status):
                """Callback for audio stream."""
                if status:
                    self.logger.warning(f"Audio stream status: {status}")
                    
                if self.is_recording:
                    # Store audio data
                    self.recorded_frames.append(indata.copy())
                    
                    # Calculate and report audio level
                    if self.level_callback:
                        rms = np.sqrt(np.mean(indata**2))
                        # Normalize to 0-1 range (assuming 16-bit audio)
                        level = min(1.0, rms * 10)
                        self.level_callback(level)
                        
            # Start audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                callback=audio_callback,
                blocksize=self.settings.audio_chunk_size
            ):
                while self.is_recording:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            self.is_recording = False
            
    def _write_wav_fallback(self, audio_data: np.ndarray) -> io.BytesIO:
        """Write WAV file using wave module as fallback.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            BytesIO buffer containing WAV data
        """
        buffer = io.BytesIO()
        
        # Convert float audio to 16-bit PCM
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            audio_data = (audio_data * 32767).astype(np.int16)
            
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
            
        return buffer


class AudioPlayer:
    """Simple audio player for WAV files."""
    
    def __init__(self):
        """Initialize audio player."""
        self.logger = logging.getLogger(__name__)
        self.is_playing = False
        self.stop_flag = threading.Event()
        
    def play(self, audio_data: Union[bytes, str]) -> bool:
        """Play audio data.
        
        Args:
            audio_data: WAV file data as bytes or path to audio file
            
        Returns:
            True if playback started successfully
        """
        if self.is_playing:
            self.logger.warning("Already playing audio")
            return False
            
        try:
            # Handle file path or bytes
            if isinstance(audio_data, str):
                # It's a file path
                tmp_path = audio_data
                cleanup_tmp = False
            else:
                # It's bytes data - save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                cleanup_tmp = True
                
            # Play using available method
            if SOUNDDEVICE_AVAILABLE and SOUNDFILE_AVAILABLE and sd is not None and sf is not None:
                return self._play_sounddevice(tmp_path)
            else:
                # Could add pygame or other fallback methods here
                self.logger.error("No audio playback library available")
                return False
                
        except Exception as e:
            self.logger.error(f"Playback error: {e}")
            return False
        finally:
            # Clean up temp file if we created one
            if 'cleanup_tmp' in locals() and cleanup_tmp and 'tmp_path' in locals():
                try:
                    Path(tmp_path).unlink()
                except:
                    pass
                    
    def _play_sounddevice(self, file_path: str) -> bool:
        """Play audio using sounddevice.
        
        Args:
            file_path: Path to WAV file
            
        Returns:
            True if playback started successfully
        """
        try:
            data, sample_rate = sf.read(file_path)
            
            self.is_playing = True
            self.stop_flag.clear()
            
            def play_thread():
                try:
                    sd.play(data, sample_rate)
                    sd.wait()  # Wait until playback is done
                except Exception as e:
                    self.logger.error(f"Playback error: {e}")
                finally:
                    self.is_playing = False
                    
            threading.Thread(target=play_thread).start()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to play audio: {e}")
            self.is_playing = False
            return False
            
    def stop(self) -> None:
        """Stop playback."""
        if self.is_playing and SOUNDDEVICE_AVAILABLE and sd is not None:
            sd.stop()
            self.is_playing = False
            

def get_audio_info(file_path: Path) -> Optional[dict]:
    """Get information about an audio file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with audio info or None if error
    """
    try:
        if SOUNDFILE_AVAILABLE and sf is not None:
            info = sf.info(str(file_path))
            return {
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype,
            }
        else:
            # Fallback to wave module for WAV files
            if file_path.suffix.lower() == '.wav':
                with wave.open(str(file_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    return {
                        'duration': frames / rate,
                        'sample_rate': rate,
                        'channels': wav_file.getnchannels(),
                        'format': 'WAV',
                        'subtype': f'{wav_file.getsampwidth() * 8}-bit',
                    }
        return None
    except Exception as e:
        logging.error(f"Error reading audio file {file_path}: {e}")
        return None


def validate_audio_file(file_path: Path, max_duration: Optional[float] = None) -> Tuple[bool, str]:
    """Validate an audio file.
    
    Args:
        file_path: Path to audio file
        max_duration: Maximum allowed duration in seconds
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, "File does not exist"
        
    if not file_path.is_file():
        return False, "Not a file"
        
    # Check file size
    settings = get_settings()
    if file_path.stat().st_size > settings.max_audio_file_size:
        return False, f"File too large (max {settings.max_audio_file_size / 1024 / 1024:.1f} MB)"
        
    # Get audio info
    info = get_audio_info(file_path)
    if info is None:
        return False, "Invalid or unsupported audio format"
        
    # Check duration
    if max_duration and info['duration'] > max_duration:
        return False, f"Audio too long (max {max_duration} seconds)"
        
    return True, ""