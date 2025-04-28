from app.models.sentiment_staking_result import SentimentStakingResult
from pydantic import ValidationError
from datetime import datetime
import pytest


def test_sentiment_staking_result_required_fields():
    now = datetime.utcnow()
    result = SentimentStakingResult(
        task_id="id1",
        status="pending",
        netuid=1,
        hotkey="hk",
        created_at=now,
        updated_at=now,
    )
    assert result.task_id == "id1"
    assert result.status == "pending"
    assert result.netuid == 1
    assert result.hotkey == "hk"
    assert result.created_at == now
    assert result.updated_at == now
    assert result.stake_amount is None
    assert result.error is None


def test_sentiment_staking_result_optional_fields():
    now = datetime.utcnow()
    result = SentimentStakingResult(
        task_id="id2",
        status="success",
        netuid=2,
        hotkey="hk2",
        stake_amount=1.23,
        error="fail",
        created_at=now,
        updated_at=now,
    )
    assert result.stake_amount == 1.23
    assert result.error == "fail"


def test_sentiment_staking_result_optional_fields_missing():
    result = SentimentStakingResult(task_id="id", status="pending", netuid=1, hotkey="hk")
    assert result.created_at is None
    assert result.updated_at is None
