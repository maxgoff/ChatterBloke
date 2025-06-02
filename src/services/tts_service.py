"""TTS service for voice cloning and generation using Chatterbox."""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Optional, Tuple
from uuid import uuid4

import numpy as np

# Try to import torch/torchaudio, but provide fallback
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from src.models import AudioOutput, VoiceProfile
from src.utils.config import get_settings


logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech generation using Chatterbox."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.settings = get_settings()
        self.model = None
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False
        
        # Job tracking
        self.active_jobs: Dict[str, Dict] = {}
        
    async def initialize(self) -> None:
        """Initialize the TTS model."""
        if self._initialized:
            return
            
        if not TORCH_AVAILABLE:
            logger.error(
                "PyTorch not available. Cannot initialize TTS. "
                "Please ensure PyTorch and torchaudio are installed."
            )
            raise ImportError("PyTorch is required but not installed")
            
        try:
            # Import here to avoid loading on startup
            from chatterbox.tts import ChatterboxTTS
            
            logger.info(f"Initializing Chatterbox TTS on {self.device}")
            
            # Load model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Load the model
            logger.info(f"Loading Chatterbox TTS model on {self.device}...")
            
            # ChatterboxTTS.from_pretrained() expects device as a parameter
            self.model = await loop.run_in_executor(
                self.executor,
                lambda: ChatterboxTTS.from_pretrained(device=self.device)
            )
            
            self._initialized = True
            logger.info("Chatterbox TTS initialized successfully")
            
        except ImportError as e:
            logger.error(
                f"Chatterbox not installed: {e}. "
                "Please install Chatterbox to use TTS functionality."
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            raise
            
    async def clone_voice(
        self,
        voice_profile_id: int,
        audio_path: Path,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Clone a voice from audio sample.
        
        Args:
            voice_profile_id: ID of the voice profile
            audio_path: Path to the audio sample
            progress_callback: Optional callback for progress updates
            
        Returns:
            Job ID for tracking progress
        """
        if not self._initialized:
            await self.initialize()
            
        job_id = str(uuid4())
        
        # Initialize job tracking
        self.active_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "voice_profile_id": voice_profile_id,
            "error": None
        }
        
        # Process in background
        asyncio.create_task(
            self._process_voice_cloning(job_id, audio_path, progress_callback)
        )
        
        return job_id
        
    async def _process_voice_cloning(
        self,
        job_id: str,
        audio_path: Path,
        progress_callback: Optional[callable] = None
    ) -> None:
        """Process voice cloning in background."""
        try:
            # Update progress
            self.active_jobs[job_id]["progress"] = 10
            if progress_callback:
                await progress_callback(10, "Loading audio file...")
                
            # Verify audio file
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
            # Update progress
            self.active_jobs[job_id]["progress"] = 30
            if progress_callback:
                await progress_callback(30, "Processing audio...")
                
            # For Chatterbox, we don't need to train - it's zero-shot
            # Just verify the audio can be loaded
            loop = asyncio.get_event_loop()
            audio, sr = await loop.run_in_executor(
                self.executor,
                torchaudio.load,
                str(audio_path)
            )
            
            # Update progress
            self.active_jobs[job_id]["progress"] = 80
            if progress_callback:
                await progress_callback(80, "Finalizing voice profile...")
                
            # Store the audio path for later use
            self.active_jobs[job_id]["audio_path"] = str(audio_path)
            
            # Complete
            self.active_jobs[job_id]["status"] = "completed"
            self.active_jobs[job_id]["progress"] = 100
            if progress_callback:
                await progress_callback(100, "Voice cloning completed!")
                
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            self.active_jobs[job_id]["status"] = "failed"
            self.active_jobs[job_id]["error"] = str(e)
            if progress_callback:
                await progress_callback(-1, f"Error: {str(e)}")
                
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a cloning job."""
        return self.active_jobs.get(job_id)
        
    async def generate_speech(
        self,
        text: str,
        voice_profile_id: Optional[int] = None,
        audio_prompt_path: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "neutral",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5
    ) -> Tuple[np.ndarray, int]:
        """Generate speech from text.
        
        Args:
            text: Text to synthesize
            voice_profile_id: Optional voice profile to use
            audio_prompt_path: Optional path to audio prompt
            speed: Speech speed multiplier
            pitch: Pitch adjustment
            emotion: Emotion style
            exaggeration: Emotion exaggeration (0-1)
            cfg_weight: Classifier-free guidance weight
            
        Returns:
            Tuple of (audio array, sample rate)
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Real generation
            loop = asyncio.get_event_loop()
            
            # Chunk text if it's too long
            # Chatterbox typically has a limit around 200-300 characters per generation
            MAX_CHUNK_LENGTH = 200
            
            logger.info(f"Generating speech for text of length {len(text)}")
            
            if len(text) > MAX_CHUNK_LENGTH:
                # Split text into sentences first, then chunks
                import re
                sentences = re.split(r'(?<=[.!?])\s+', text)
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= MAX_CHUNK_LENGTH:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk)
                    
                # If a single sentence is too long, split by words
                final_chunks = []
                for chunk in chunks:
                    if len(chunk) > MAX_CHUNK_LENGTH:
                        words = chunk.split()
                        temp_chunk = ""
                        for word in words:
                            if len(temp_chunk) + len(word) + 1 <= MAX_CHUNK_LENGTH:
                                temp_chunk += (" " if temp_chunk else "") + word
                            else:
                                if temp_chunk:
                                    final_chunks.append(temp_chunk)
                                temp_chunk = word
                        if temp_chunk:
                            final_chunks.append(temp_chunk)
                    else:
                        final_chunks.append(chunk)
                
                # Generate audio for each chunk
                wav_chunks = []
                logger.info(f"Processing {len(final_chunks)} chunks")
                for i, chunk in enumerate(final_chunks):
                    logger.info(f"Generating chunk {i+1}/{len(final_chunks)}: {len(chunk)} chars")
                    gen_kwargs = {
                        "text": chunk,
                        "exaggeration": exaggeration,
                        "cfg_weight": cfg_weight
                    }
                    
                    if audio_prompt_path:
                        gen_kwargs["audio_prompt_path"] = audio_prompt_path
                        
                    chunk_wav = await loop.run_in_executor(
                        self.executor,
                        lambda c=chunk, k=gen_kwargs: self.model.generate(**k)
                    )
                    wav_chunks.append(chunk_wav)
                
                # Concatenate all chunks with a small pause between them
                # First, ensure all chunks have the same number of channels
                processed_chunks = []
                for chunk in wav_chunks:
                    # Convert to numpy if it's a tensor
                    if hasattr(chunk, 'cpu'):
                        chunk_np = chunk.cpu().numpy()
                    else:
                        chunk_np = chunk
                        
                    if chunk_np.ndim == 1:
                        # Single channel audio
                        processed_chunks.append(chunk_np)
                    else:
                        # Multi-channel, take first channel or average
                        if chunk_np.shape[0] < chunk_np.shape[1]:
                            # Shape is (channels, samples)
                            processed_chunks.append(chunk_np[0])
                        else:
                            # Shape is (samples, channels)
                            processed_chunks.append(chunk_np[:, 0])
                
                # Add small silence between chunks (0.1 second)
                silence_samples = int(self.model.sr * 0.1)
                silence = np.zeros(silence_samples)
                
                # Concatenate with silence between chunks
                wav_with_pauses = []
                for i, chunk in enumerate(processed_chunks):
                    wav_with_pauses.append(chunk)
                    if i < len(processed_chunks) - 1:
                        wav_with_pauses.append(silence)
                
                wav = np.concatenate(wav_with_pauses)
                
            else:
                # Text is short enough, generate normally
                gen_kwargs = {
                    "text": text,
                    "exaggeration": exaggeration,
                    "cfg_weight": cfg_weight
                }
                
                # Add audio prompt if provided
                if audio_prompt_path:
                    gen_kwargs["audio_prompt_path"] = audio_prompt_path
                elif voice_profile_id:
                    # Look up audio path from voice profile
                    # This would need database access
                    pass
                    
                # Generate audio
                wav = await loop.run_in_executor(
                    self.executor,
                    lambda: self.model.generate(**gen_kwargs)
                )
            
            # Apply speed adjustment if needed
            if speed != 1.0:
                wav = self._adjust_speed(wav, speed)
                
            # Apply pitch adjustment if needed
            if pitch != 1.0:
                wav = self._adjust_pitch(wav, pitch, self.model.sr)
                
            # Convert to numpy array if it's a tensor
            if hasattr(wav, 'cpu'):
                audio_array = wav.cpu().numpy()
            else:
                audio_array = wav
                
            if audio_array.ndim > 1:
                audio_array = audio_array.squeeze()
                
            return audio_array, self.model.sr
            
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise
            
    def _adjust_speed(self, audio, speed: float):
        """Adjust audio playback speed."""
        if not TORCH_AVAILABLE or speed == 1.0:
            return audio
            
        # Resample to adjust speed
        orig_len = audio.shape[-1]
        new_len = int(orig_len / speed)
        
        # Use linear interpolation for speed adjustment
        if audio.ndim == 1:
            audio = audio.unsqueeze(0)
            
        adjusted = torch.nn.functional.interpolate(
            audio.unsqueeze(0),
            size=new_len,
            mode='linear',
            align_corners=False
        ).squeeze(0)
        
        return adjusted
        
    def _adjust_pitch(
        self,
        audio,
        pitch_factor: float,
        sample_rate: int
    ):
        """Adjust audio pitch."""
        if not TORCH_AVAILABLE or pitch_factor == 1.0:
            return audio
            
        # Simple pitch shifting using resampling
        # For better quality, we'd use a proper pitch shifting algorithm
        return audio  # Placeholder for now
        
    async def save_output(
        self,
        audio_array: np.ndarray,
        sample_rate: int,
        script_id: int,
        voice_profile_id: int,
        format: str = "wav"
    ) -> Path:
        """Save generated audio to file.
        
        Args:
            audio_array: Audio data
            sample_rate: Sample rate
            script_id: Associated script ID
            voice_profile_id: Voice profile used
            format: Output format (wav, mp3, etc.)
            
        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{script_id}_{voice_profile_id}_{timestamp}.{format}"
        output_path = self.settings.outputs_dir / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save audio
        loop = asyncio.get_event_loop()
        
        if TORCH_AVAILABLE:
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio_array)
            if audio_tensor.ndim == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
                
            await loop.run_in_executor(
                self.executor,
                torchaudio.save,
                str(output_path),
                audio_tensor,
                sample_rate
            )
        else:
            # Use soundfile as fallback
            import soundfile as sf
            await loop.run_in_executor(
                self.executor,
                sf.write,
                str(output_path),
                audio_array,
                sample_rate
            )
        
        logger.info(f"Saved audio output to {output_path}")
        return output_path
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        if self.model:
            del self.model
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get or create the global TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


from datetime import datetime