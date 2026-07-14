"""Admin coupon management schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.common.enums import CouponType


class CouponCreateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    coupon_type: CouponType
    value: Decimal = Field(..., ge=0)
    minimum_order_amount: Decimal | None = Field(default=None, ge=0)
    maximum_discount: Decimal | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=0)
    per_user_limit: int | None = Field(default=None, ge=0)
    is_active: bool = True
    starts_at: datetime | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_coupon(self) -> CouponCreateRequest:
        if self.coupon_type == CouponType.PERCENTAGE and self.value > 100:
            raise ValueError("Percentage coupons cannot exceed 100")
        if self.starts_at and self.expires_at and self.expires_at < self.starts_at:
            raise ValueError("expires_at must be after starts_at")
        return self


class CouponUpdateRequest(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    coupon_type: CouponType | None = None
    value: Decimal | None = Field(default=None, ge=0)
    minimum_order_amount: Decimal | None = Field(default=None, ge=0)
    maximum_discount: Decimal | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=0)
    per_user_limit: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CouponResponse(BaseModel):
    id: UUID
    code: str
    description: str | None
    coupon_type: CouponType
    value: Decimal
    minimum_order_amount: Decimal | None
    maximum_discount: Decimal | None
    usage_limit: int | None
    per_user_limit: int | None
    used_count: int
    is_active: bool
    starts_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CouponUsageReportResponse(BaseModel):
    coupon_id: UUID
    code: str
    used_count: int
    usage_limit: int | None
    total_discount_applied: Decimal
    unique_users: int
    remaining_uses: int | None


class CouponFilterParams(BaseModel):
    q: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    coupon_type: CouponType | None = None
    sort: str = Field(default="newest", pattern="^(newest|oldest|usage)$")
