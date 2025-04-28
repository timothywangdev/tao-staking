import pytest
from unittest.mock import MagicMock, patch
from app.clients.desearch import DesearchClient


@pytest.fixture
def desearch_client():
    with patch("app.clients.desearch.Desearch") as mock_desearch_cls:
        mock_desearch = MagicMock()
        mock_desearch_cls.return_value = mock_desearch
        client = DesearchClient()
        client.client = mock_desearch
        yield client, mock_desearch


def test_search_tweets(desearch_client):
    client, mock_desearch = desearch_client
    mock_desearch.basic_twitter_search.return_value = [
        {"text": "tweet1"},
        {"text": "tweet2"},
    ]
    result = client.search_tweets("query", 2)
    assert result == ["tweet1", "tweet2"]
    mock_desearch.basic_twitter_search.assert_called_once_with(query="query")
