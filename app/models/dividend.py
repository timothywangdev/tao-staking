from pydantic import BaseModel
from typing import Optional


class DividendResponse(BaseModel):
    netuid: int
    hotkey: str
    dividend: float
    cached: bool = False
    stake_tx_triggered: bool = False


class DividendRequest(BaseModel):
    netuid: Optional[int] = None
    hotkey: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
