import pytest
import pytest_asyncio
from fastapi import status, Depends
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models.dividend import DividendResponse, ErrorResponse
import app.api.v1.tao_dividends as tao_dividends_module
from httpx import ASGITransport, AsyncClient
import asyncio

# Constants for test
TEST_NETUID = 42
TEST_HOTKEY = "test_hotkey"
TEST_DIVIDEND = 123.45
SECRET_KEY = "secret_key"

# Patch settings for test
app.dependency_overrides = {}


def override_get_api_key():
    return SECRET_KEY


app.dependency_overrides[tao_dividends_module.get_api_key] = override_get_api_key


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_get_tao_dividends_cache_hit(async_client):
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=TEST_DIVIDEND)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock()

        response = await async_client.get(
            f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["netuid"] == TEST_NETUID
        assert data["hotkey"] == TEST_HOTKEY
        assert data["dividend"] == TEST_DIVIDEND
        assert data["cached"] is True
        assert data["stake_tx_triggered"] is False
        mock_cache_client.get.assert_awaited_once()
        mock_bt_client.get_dividend.assert_not_awaited()


@pytest.mark.anyio
async def test_get_tao_dividends_cache_miss(async_client):
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock(return_value=TEST_DIVIDEND)

        response = await async_client.get(
            f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["netuid"] == TEST_NETUID
        assert data["hotkey"] == TEST_HOTKEY
        assert data["dividend"] == TEST_DIVIDEND
        assert data["cached"] is False
        assert data["stake_tx_triggered"] is False
        mock_cache_client.get.assert_awaited_once()
        mock_bt_client.get_dividend.assert_awaited_once_with(TEST_NETUID, TEST_HOTKEY)
        mock_cache_client.set.assert_awaited_once()


@pytest.mark.anyio
async def test_get_tao_dividends_blockchain_error(async_client):
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock(side_effect=Exception("blockchain error"))

        response = await async_client.get(
            f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "Failed to query blockchain" in data["detail"]


@pytest.mark.anyio
async def test_get_tao_dividends_cache_error(async_client):
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(side_effect=Exception("cache error"))
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock(return_value=TEST_DIVIDEND)

        response = await async_client.get(
            f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["netuid"] == TEST_NETUID
        assert data["hotkey"] == TEST_HOTKEY
        assert data["dividend"] == TEST_DIVIDEND
        assert data["cached"] is False
        assert data["stake_tx_triggered"] is False
        mock_cache_client.get.assert_awaited_once()
        mock_bt_client.get_dividend.assert_awaited_once_with(TEST_NETUID, TEST_HOTKEY)
        mock_cache_client.set.assert_awaited_once()


@pytest.mark.anyio
async def test_get_tao_dividends_trade_triggers_task(async_client):
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
        patch.object(tao_dividends_module, "sentiment_staking_task") as mock_task,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=TEST_DIVIDEND)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock()
        mock_task.delay = MagicMock()

        response = await async_client.get(
            f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}&trade=true",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stake_tx_triggered"] is True
        mock_task.delay.assert_called_once_with(TEST_NETUID, TEST_HOTKEY)


@pytest.mark.anyio
async def test_get_tao_dividends_defaults(async_client):
    # Test default netuid and hotkey from settings
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        from app.config import settings

        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=TEST_DIVIDEND)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock()

        response = await async_client.get(
            "/api/v1/tao_dividends",
            headers={"X-API-Key": SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["netuid"] == settings.DEFAULT_NETUID
        assert data["hotkey"] == settings.DEFAULT_HOTKEY


@pytest.mark.anyio
async def test_get_tao_dividends_concurrent(async_client):
    """
    Simulate many concurrent requests to the /api/v1/tao_dividends endpoint
    to ensure the service can handle concurrent access.
    """
    with (
        patch.object(tao_dividends_module, "cache_client") as mock_cache_client,
        patch.object(tao_dividends_module, "bittensor_client") as mock_bt_client,
    ):
        mock_cache_client.build_cache_key.return_value = "cache:key"
        mock_cache_client.get = AsyncMock(return_value=TEST_DIVIDEND)
        mock_cache_client.set = AsyncMock()
        mock_bt_client.get_dividend = AsyncMock()

        # Define a single request coroutine
        async def make_request():
            response = await async_client.get(
                f"/api/v1/tao_dividends?netuid={TEST_NETUID}&hotkey={TEST_HOTKEY}",
                headers={"X-API-Key": SECRET_KEY},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["netuid"] == TEST_NETUID
            assert data["hotkey"] == TEST_HOTKEY
            assert data["dividend"] == TEST_DIVIDEND
            assert data["cached"] is True
            assert data["stake_tx_triggered"] is False
            return data

        # Simulate 20 concurrent requests
        results = await asyncio.gather(*(make_request() for _ in range(20)))
        assert len(results) == 20
        # Optionally, check that all results are identical
        for result in results:
            assert result["dividend"] == TEST_DIVIDEND
