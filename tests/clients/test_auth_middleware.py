import pytest
from fastapi import HTTPException, status
from unittest.mock import patch
from app.middleware.auth import get_api_key


@pytest.mark.asyncio
async def test_get_api_key_valid():
    with (
        patch("app.middleware.auth.settings.SECRET_KEY", "secret"),
        patch("app.middleware.auth.API_KEY_HEADER", new=lambda: None),
    ):
        result = await get_api_key(api_key="secret")
        assert result == "secret"


@pytest.mark.asyncio
async def test_get_api_key_invalid():
    with (
        patch("app.middleware.auth.settings.SECRET_KEY", "secret"),
        patch("app.middleware.auth.API_KEY_HEADER", new=lambda: None),
    ):
        with pytest.raises(HTTPException) as exc:
            await get_api_key(api_key="wrong")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.value.detail == "Invalid API key"


@pytest.mark.asyncio
async def test_get_api_key_missing():
    with (
        patch("app.middleware.auth.settings.SECRET_KEY", "secret"),
        patch("app.middleware.auth.API_KEY_HEADER", new=lambda: None),
    ):
        with pytest.raises(HTTPException) as exc:
            await get_api_key(api_key=None)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
