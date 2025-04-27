from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import Field, validator, AnyHttpUrl, DirectoryPath
import secrets
import os
from pathlib import Path

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod")
    )

    # API Settings
    API_V1_STR: str = Field("/api/v1", description="API version prefix")
    PROJECT_NAME: str = Field("Tao Dividends API", description="Project name")
    DEBUG: bool = Field(False, description="Debug mode")

    # Authentication
    SECRET_KEY: str = Field(description="Secret key for JWT tokens and API keys")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30, description="Access token expiry time in minutes", gt=0
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        60, description="Number of requests allowed per minute", gt=0
    )
    RATE_LIMIT_BURST: int = Field(100, description="Maximum burst size for rate limiting", gt=0)
    RATE_LIMIT_STORAGE_URL: str = Field(
        "redis://localhost:6379/0", description="Redis URL for rate limit storage"
    )

    # MongoDB
    MONGODB_URL: str = Field("mongodb://localhost:27017", description="MongoDB connection URL")
    MONGODB_DB_NAME: str = Field("tao_dividends", description="MongoDB database name")

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/1", description="Redis URL for caching")
    REDIS_POOL_SIZE: int = Field(100, description="Redis connection pool size", gt=0)

    # Bittensor
    BITTENSOR_NETWORK: str = Field("test", description="Bittensor network (test or mainnet)")
    BITTENSOR_WALLET_PATH: Optional[str] = Field(None, description="Path to Bittensor wallet")
    BITTENSOR_WALLET_NAME: Optional[str] = Field(None, description="Name of Bittensor wallet")
    BITTENSOR_WALLET_MNEMONIC: str = Field(..., description="Mnemonic for Bittensor wallet")
    DEFAULT_HOTKEY: str = Field(
        "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", description="Default hotkey for queries"
    )
    DEFAULT_NETUID: int = Field(18, description="Default subnet ID", ge=0)

    # Datura API
    DATURA_API_KEY: str = Field(..., description="API key for Datura")

    # Chutes API
    CHUTES_API_KEY: str = Field(..., description="API key for Chutes LLM service")

    @validator("BITTENSOR_NETWORK")
    def validate_network(cls, v: str) -> str:
        if v not in ["test", "main"]:
            raise ValueError("BITTENSOR_NETWORK must be either 'test' or 'main'")
        return v

    @validator("MONGODB_URL")
    def validate_mongodb_url(cls, v: str) -> str:
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URL must start with mongodb:// or mongodb+srv://")
        return v

    @validator("REDIS_URL", "RATE_LIMIT_STORAGE_URL")
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError("Redis URLs must start with redis://")
        return v


settings = Settings()
