from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SentimentStakingResult(BaseModel):
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status: pending, success, or failed")
    netuid: int = Field(..., description="Subnet ID")
    hotkey: str = Field(..., description="Hotkey address")
    stake_amount: Optional[float] = Field(None, description="Stake or unstake amount")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Task last update timestamp")
    # Add any additional fields as needed
