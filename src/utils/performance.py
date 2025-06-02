"""Performance monitoring utilities."""

import time
import logging
from functools import wraps
from typing import Callable, Any


logger = logging.getLogger(__name__)


def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        if duration > 1.0:  # Log if takes more than 1 second
            logger.warning(f"{func.__name__} took {duration:.2f} seconds")
        else:
            logger.debug(f"{func.__name__} took {duration:.3f} seconds")
            
        return result
    return wrapper


async def measure_async_time(func: Callable) -> Callable:
    """Decorator to measure async function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        if duration > 1.0:  # Log if takes more than 1 second
            logger.warning(f"{func.__name__} took {duration:.2f} seconds")
        else:
            logger.debug(f"{func.__name__} took {duration:.3f} seconds")
            
        return result
    return wrapper


class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {
            "api_calls": 0,
            "api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "audio_recordings": 0,
            "tts_generations": 0,
            "script_saves": 0,
        }
        self.start_time = time.time()
        
    def increment(self, metric: str, count: int = 1) -> None:
        """Increment a metric counter."""
        if metric in self.metrics:
            self.metrics[metric] += count
            
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time
        
    def get_summary(self) -> dict:
        """Get performance summary."""
        uptime = self.get_uptime()
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_duration(uptime),
            "metrics": self.metrics.copy(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }
        
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total == 0:
            return 0.0
        return (self.metrics["cache_hits"] / total) * 100
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


# Global performance monitor
performance_monitor = PerformanceMonitor()