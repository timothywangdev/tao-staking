import pytest
from unittest.mock import MagicMock, patch
from app.clients.chutes import ChutesClient


@pytest.fixture
def chutes_client():
    with patch("app.clients.chutes.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        with patch("app.clients.chutes.settings.CHUTES_API_KEY", "token"):
            client = ChutesClient()
            client.client = mock_client
            yield client, mock_client


def test_get_headers(chutes_client):
    client, _ = chutes_client
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer token"
    assert headers["Content-Type"] == "application/json"


def test_close(chutes_client):
    client, mock_client = chutes_client
    client.close()
    mock_client.close.assert_called_once()


def test_chat_completions(chutes_client):
    client, mock_client = chutes_client
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "42"}}]}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    result = client._chat_completions("prompt")
    assert result == "42"
    mock_client.post.assert_called_once()


def test_get_sentiment_score(chutes_client):
    client, _ = chutes_client
    with patch.object(client, "_chat_completions", return_value="10"):
        score = client.get_sentiment_score(["tweet1", "tweet2"])
        assert score == 10
