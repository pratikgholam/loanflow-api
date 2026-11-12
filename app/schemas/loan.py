"""Loan application request/response Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import LoanStatus


class LoanApplicationCreate(BaseModel):
    amount: float = Field(gt=0)
    purpose: str = Field(min_length=1, max_length=1000)


class LoanApplicationRead(BaseModel):
    id: int
    user_id: int
    amount: float
    purpose: str
    status: LoanStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoanStatusUpdate(BaseModel):
    status: LoanStatus
    reason: Optional[str] = Field(default=None, max_length=500)
