import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.clients.wallet import WalletClient


@pytest.fixture
def wallet_client():
    with patch("app.clients.wallet.Wallet") as mock_wallet_cls:
        mock_wallet = MagicMock()
        mock_wallet_cls.return_value = mock_wallet
        mock_wallet.coldkey_file.exists_on_device.return_value = True
        client = WalletClient()
        client.wallet = mock_wallet
        yield client, mock_wallet


def test_get_wallet(wallet_client):
    client, mock_wallet = wallet_client
    assert client.get_wallet() is mock_wallet


@pytest.mark.asyncio
async def test_get_balance(wallet_client):
    client, mock_wallet = wallet_client
    mock_wallet.get_balance = AsyncMock(return_value=123.45)
    result = await client.get_balance()
    assert result == 123.45
