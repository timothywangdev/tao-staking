import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.tasks.sentiment_staking_task import sentiment_staking


@pytest.mark.asyncio
async def test_sentiment_staking_success():
    # Arrange: create mocks
    mock_mongo = AsyncMock()
    mock_bittensor = AsyncMock()
    mock_wallet = MagicMock()
    mock_desearch = MagicMock()
    mock_chutes = MagicMock()

    # Set up return values
    mock_desearch.search_tweets.return_value = ["tweet1", "tweet2"]
    mock_chutes.get_sentiment_score.return_value = 5
    mock_bittensor.stake.return_value = True
    mock_wallet.get_wallet.return_value = "mock_wallet"

    # Act
    result = await sentiment_staking(
        netuid=1,
        hotkey="hotkey",
        task_id="task123",
        mongo_client=mock_mongo,
        bittensor_client=mock_bittensor,
        wallet_client=mock_wallet,
        desearch_client=mock_desearch,
        chutes_client=mock_chutes,
        stake_amount_fn=lambda score: 1.5,  # Custom logic for test
    )

    # Assert
    assert result["status"] == "success"
    assert result["stake_amount"] == 1.5
    mock_mongo.insert_one.assert_awaited()
    mock_mongo.update_one.assert_awaited()
    mock_bittensor.stake.assert_awaited_with("mock_wallet", 1, "hotkey", 1.5)


@pytest.mark.asyncio
async def test_sentiment_staking_failure_on_stake():
    # Arrange: create mocks
    mock_mongo = AsyncMock()
    mock_bittensor = AsyncMock()
    mock_wallet = MagicMock()
    mock_desearch = MagicMock()
    mock_chutes = MagicMock()

    # Set up return values
    mock_desearch.search_tweets.return_value = ["tweet1", "tweet2"]
    mock_chutes.get_sentiment_score.return_value = 5
    mock_bittensor.stake.return_value = False
    mock_wallet.get_wallet.return_value = "mock_wallet"

    # Act
    result = await sentiment_staking(
        netuid=1,
        hotkey="hotkey",
        task_id="task123",
        mongo_client=mock_mongo,
        bittensor_client=mock_bittensor,
        wallet_client=mock_wallet,
        desearch_client=mock_desearch,
        chutes_client=mock_chutes,
    )

    # Assert
    assert result["status"] == "failed"
    mock_mongo.insert_one.assert_awaited()
    mock_mongo.update_one.assert_awaited()
    mock_bittensor.stake.assert_awaited()


# Add more tests for exceptions, unstake, etc.
