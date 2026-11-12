"""User request/response Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
