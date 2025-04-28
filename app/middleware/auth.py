from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from ..config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


async def get_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """Validate API key from header."""
    print(f"api_key: {api_key}", "settings.SECRET_KEY: ", settings.SECRET_KEY)
    if api_key == settings.SECRET_KEY:  # In production, use a proper API key validation
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
