"""Admin customer management schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import UserRole
from app.schemas.users import UserProfileResponse


class AdminCustomerFilterParams(BaseModel):
    q: str | None = Field(default=None, max_length=150)
    name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    sort: str = Field(default="newest", pattern="^(newest|oldest|name)$")


class AdminCustomerUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None


class AdminCustomerStatusRequest(BaseModel):
    is_active: bool


class AdminCustomerDetailResponse(UserProfileResponse):
    updated_at: datetime
    order_count: int = 0
