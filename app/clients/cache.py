import redis.asyncio as redis
from ..config import settings
import json
from typing import Optional, Dict, Any


class CacheClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.default_ttl = 120  # 2 minutes

    async def get_dividend_cache_key(self, netuid: int, hotkey: str) -> str:
        """Generate cache key for dividend data."""
        return f"tao:dividend:{netuid}:{hotkey}"

    async def get_cached_dividend(self, netuid: int, hotkey: str) -> Optional[Dict[str, Any]]:
        """Get cached dividend data if it exists."""
        try:
            key = await self.get_dividend_cache_key(netuid, hotkey)
            data = await self.redis.get(key)
            return json.loads(data) if data else None

        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache get error: {str(e)}")
            return None

    async def set_cached_dividend(
        self, netuid: int, hotkey: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """Cache dividend data with TTL."""
        try:
            key = await self.get_dividend_cache_key(netuid, hotkey)
            await self.redis.setex(key, ttl or self.default_ttl, json.dumps(data))

        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache set error: {str(e)}")
            pass
