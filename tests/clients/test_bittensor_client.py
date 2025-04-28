import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.clients.bittensor import BitTensorClient


@pytest.fixture
def bittensor_client():
    with patch("app.clients.bittensor.AsyncSubtensor") as mock_subtensor:
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        client = BitTensorClient()
        client.subtensor = mock_instance
        yield client


@pytest.mark.asyncio
async def test_get_dividends_for_subnet(bittensor_client):
    mock_async_subtensor = MagicMock()
    mock_result = [(b"key", MagicMock(value=42))]

    async def async_iter():
        for k, v in mock_result:
            yield k, v

    mock_async_subtensor.substrate.query_map = AsyncMock(
        return_value=MagicMock(__aiter__=lambda s: async_iter())
    )
    bittensor_client.subtensor.__aenter__.return_value = mock_async_subtensor
    with patch("app.clients.bittensor.decode_account_id", return_value="hotkey1"):
        result = await bittensor_client.get_dividends_for_subnet(1)
        assert result == {"hotkey1": 42}


@pytest.mark.asyncio
async def test_get_dividend(bittensor_client):
    with patch.object(
        bittensor_client, "get_dividends_for_subnet", AsyncMock(return_value={"hk": 1.23})
    ):
        val = await bittensor_client.get_dividend(1, "hk")
        assert val == 1.23


@pytest.mark.asyncio
async def test_stake_success(bittensor_client):
    mock_wallet = MagicMock()
    mock_async_subtensor = MagicMock()
    mock_async_subtensor.add_stake = AsyncMock(return_value=True)
    bittensor_client.subtensor.__aenter__.return_value = mock_async_subtensor
    with patch("app.clients.bittensor.tao", return_value=10):
        result = await bittensor_client.stake(mock_wallet, 1, "hk", 5)
        assert result is True


@pytest.mark.asyncio
async def test_unstake_success(bittensor_client):
    mock_wallet = MagicMock()
    mock_async_subtensor = MagicMock()
    mock_async_subtensor.unstake = AsyncMock(return_value=True)
    bittensor_client.subtensor.__aenter__.return_value = mock_async_subtensor
    with patch("app.clients.bittensor.tao", return_value=10):
        result = await bittensor_client.unstake(mock_wallet, 1, "hk", 5)
        assert result is True
