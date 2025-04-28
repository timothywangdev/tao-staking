import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.clients.cache import CacheClient


@pytest.fixture
def cache_client():
    with patch("app.clients.cache.redis.from_url") as mock_redis:
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        client = CacheClient()
        client.redis = mock_redis_instance
        yield client


def test_build_cache_key(cache_client):
    key = cache_client.build_cache_key(1, "abc", prefix="foo")
    assert key == "foo:1:abc"
    key2 = cache_client.build_cache_key(1, "abc")
    assert key2 == "1:abc"


@pytest.mark.asyncio
async def test_get_returns_value(cache_client):
    cache_client.redis.get = AsyncMock(return_value=b"123")
    with patch("app.clients.cache.json.loads", return_value=123):
        val = await cache_client.get("key")
        assert val == 123


@pytest.mark.asyncio
async def test_get_returns_none_on_exception(cache_client):
    cache_client.redis.get = AsyncMock(side_effect=Exception("fail"))
    val = await cache_client.get("key")
    assert val is None


@pytest.mark.asyncio
async def test_set_success(cache_client):
    cache_client.redis.setex = AsyncMock()
    with patch("app.clients.cache.json.dumps", return_value="data"):
        await cache_client.set("key", {"foo": "bar"})
        cache_client.redis.setex.assert_awaited()
