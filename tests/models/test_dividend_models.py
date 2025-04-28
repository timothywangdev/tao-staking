from app.models.dividend import DividendResponse, DividendRequest, ErrorResponse
from pydantic import ValidationError
import pytest


def test_dividend_response_required_fields():
    resp = DividendResponse(netuid=1, hotkey="hk", dividend=1.23)
    assert resp.netuid == 1
    assert resp.hotkey == "hk"
    assert resp.dividend == 1.23
    assert resp.cached is False
    assert resp.stake_tx_triggered is False


def test_dividend_response_defaults():
    resp = DividendResponse(netuid=1, hotkey="hk", dividend=1.23)
    assert resp.cached is False
    assert resp.stake_tx_triggered is False


def test_dividend_response_validation():
    with pytest.raises(ValidationError):
        DividendResponse(netuid=1, hotkey="hk")  # missing dividend


def test_dividend_request_optional():
    req = DividendRequest()
    assert req.netuid is None
    assert req.hotkey is None
    req2 = DividendRequest(netuid=2, hotkey="abc")
    assert req2.netuid == 2
    assert req2.hotkey == "abc"


def test_error_response_fields():
    err = ErrorResponse(error="fail", detail="bad")
    assert err.error == "fail"
    assert err.detail == "bad"
    err2 = ErrorResponse(error="fail")
    assert err2.detail is None
