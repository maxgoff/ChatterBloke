"""GUI services for API communication."""

import asyncio
import logging
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.api.client import APIClient
from src.utils.config import get_settings


logger = logging.getLogger(__name__)


class APIService(QObject):
    """Service for managing API communication in the GUI."""
    
    # Signals
    connected = pyqtSignal(bool)  # Emitted when connection status changes
    error = pyqtSignal(str)       # Emitted on API errors
    
    def __init__(self):
        """Initialize API service."""
        super().__init__()
        self.settings = get_settings()
        self.client: Optional[APIClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[QThread] = None
        self._running = False
        
    def start(self):
        """Start the API service in a separate thread."""
        if self._thread is not None:
            return
            
        self._running = True
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)
        self._thread.start()
        
    def stop(self):
        """Stop the API service."""
        self._running = False
        
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop).result(timeout=2.0)
            
        if self._thread:
            self._thread.quit()
            if not self._thread.wait(5000):  # Wait up to 5 seconds
                logger.warning("API service thread did not stop cleanly")
            self._thread = None
            
    def _run(self):
        """Run the event loop in the thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Create API client
        self.client = APIClient()
        
        # Check connection
        self._loop.run_until_complete(self._check_connection())
        
        # Set up periodic connection checks
        self._loop.create_task(self._periodic_connection_check())
        
        # Keep the loop running
        self._loop.run_forever()
        
    async def _cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.close()
            self.client = None
            
        if self._loop:
            self._loop.stop()
            
    async def _check_connection(self):
        """Check API connection."""
        try:
            is_healthy = await self.client.health_check()
            self.connected.emit(is_healthy)
            if is_healthy:
                logger.info("Connected to API server")
            else:
                logger.warning("API server is not healthy")
        except Exception as e:
            logger.warning(f"API server not available: {e}")
            self.connected.emit(False)
            # Don't emit error signal on initial connection attempt
            # This allows the app to run in offline mode
            
    def run_async(self, coro):
        """Run an async coroutine and return a future."""
        if not self._loop:
            raise RuntimeError("API service not started")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
        
    async def _periodic_connection_check(self):
        """Periodically check API connection status."""
        while self._running:
            await asyncio.sleep(60)  # Check every 60 seconds
            if self._running:
                await self._check_connection()


# Global API service instance
_api_service: Optional[APIService] = None


def get_api_service() -> APIService:
    """Get or create the global API service instance."""
    global _api_service
    if _api_service is None:
        _api_service = APIService()
        _api_service.start()
    return _api_service


class AsyncWorker(QThread):
    """Worker thread for running async operations."""
    
    # Signals
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, coro_func, *args, **kwargs):
        """Initialize async worker.
        
        Args:
            coro_func: Async function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
        """
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        """Run the async operation."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.coro_func(*self.args, **self.kwargs)
            )
            self.result.emit(result)
        except Exception as e:
            logger.error(f"Async worker error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()