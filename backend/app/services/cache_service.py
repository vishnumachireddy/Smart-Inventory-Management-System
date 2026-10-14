import time
import threading
from typing import Any, Dict, Optional, Tuple


class FastInMemoryCache:
    """
    High-performance in-memory cache with thread-safe access and TTL expiration.
    Eliminates repetitive high-latency database network round-trips to remote Neon PostgreSQL.
    """

    def __init__(self):
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieves cached item if present and not expired."""
        with self._lock:
            if key not in self._store:
                return None
            expiry, value = self._store[key]
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int = 30):
        """Stores item with TTL in seconds."""
        with self._lock:
            self._store[key] = (time.time() + ttl_seconds, value)

    def invalidate(self, *prefixes_or_keys: str):
        """Invalidates all cache entries matching specified keys or key prefixes."""
        with self._lock:
            if not prefixes_or_keys:
                self._store.clear()
                return

            keys_to_delete = []
            for stored_key in self._store:
                for target in prefixes_or_keys:
                    if stored_key == target or stored_key.startswith(target):
                        keys_to_delete.append(stored_key)
                        break

            for k in keys_to_delete:
                self._store.pop(k, None)

    def clear(self):
        """Purges all cached data."""
        with self._lock:
            self._store.clear()


# Global cache instance
data_cache = FastInMemoryCache()
