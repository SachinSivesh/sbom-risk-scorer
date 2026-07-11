"""Redis cache wrapper for vulnerability and maintenance data caching."""

import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.config import get_settings


class RedisCache:
    """Async Redis cache wrapper with JSON serialization."""

    def __init__(self):
        settings = get_settings()
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key, returns None on miss."""
        try:
            value = await self._redis.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a cached value with TTL in seconds."""
        try:
            await self._redis.set(key, json.dumps(value), ex=ttl)
        except Exception:
            pass  # Cache failures should never break the application

    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        try:
            await self._redis.delete(key)
        except Exception:
            pass

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.close()


# Singleton instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get or create the singleton cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
