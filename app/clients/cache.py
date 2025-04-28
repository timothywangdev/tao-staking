import redis.asyncio as redis
from ..config import settings
import json
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.default_ttl = settings.REDIS_CACHE_TTL

    def build_cache_key(self, *args, prefix: Optional[str] = None) -> str:
        """Build a cache key from prefix and args."""
        key_parts = [prefix] if prefix else []
        key_parts += [str(arg) for arg in args]
        return ":".join(key_parts)

    async def get(self, key: str) -> Optional[Any]:
        """Get cached data by key."""
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set cached data by key with TTL."""
        try:
            await self.redis.setex(key, ttl or self.default_ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            pass
