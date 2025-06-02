"""Simple in-memory cache for performance optimization."""

import time
from typing import Any, Dict, Optional, Tuple


class SimpleCache:
    """Simple time-based in-memory cache."""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                # Expired, remove it
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
        
    def invalidate(self, key: str) -> None:
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]
            
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        
    def cleanup_expired(self) -> None:
        """Remove all expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time >= expiry
        ]
        for key in expired_keys:
            del self.cache[key]


# Global caches for different data types
script_cache = SimpleCache(ttl=600)  # 10 minutes for scripts
voice_cache = SimpleCache(ttl=300)   # 5 minutes for voice profiles
model_cache = SimpleCache(ttl=3600)  # 1 hour for LLM models