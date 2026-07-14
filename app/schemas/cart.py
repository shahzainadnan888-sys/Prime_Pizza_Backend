"""Cart, wishlist, checkout, and coupon schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.common.enums import CartStatus, CouponType


class CartExtraInput(BaseModel):
    option_id: UUID
    quantity: int = Field(default=1, ge=1, le=10)


class AddCartItemRequest(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    quantity: int = Field(default=1, ge=1, le=100)
    extra_option_ids: list[UUID] = Field(default_factory=list)
    extras: list[CartExtraInput] = Field(default_factory=list)
    special_instructions: str | None = Field(default=None, max_length=500)

    @field_validator("extra_option_ids")
    @classmethod
    def dedupe_option_ids(cls, value: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(value))


class UpdateCartItemRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=1, le=100)
    special_instructions: str | None = Field(default=None, max_length=500)
    extra_option_ids: list[UUID] | None = None
    extras: list[CartExtraInput] | None = None


class ApplyCouponRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class WishlistAddRequest(BaseModel):
    product_id: UUID


class CartItemExtraResponse(BaseModel):
    option_id: UUID
    name: str | None = None
    quantity: int
    unit_price: Decimal

    model_config = {"from_attributes": True}


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str | None = None
    product_slug: str | None = None
    variant_id: UUID | None = None
    variant_name: str | None = None
    quantity: int
    unit_price: Decimal
    discount_price: Decimal | None = None
    subtotal: Decimal
    special_instructions: str | None = None
    extras: list[CartItemExtraResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: UUID
    status: CartStatus
    currency: str
    notes: str | None = None
    last_activity: datetime | None = None
    coupon_id: UUID | None = None
    coupon_code: str | None = None
    subtotal: Decimal
    discount: Decimal
    delivery_fee: Decimal
    tax: Decimal
    grand_total: Decimal
    item_count: int = 0
    items: list[CartItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderSummaryLineResponse(BaseModel):
    product_id: UUID
    product_name: str
    variant_name: str | None = None
    quantity: int
    unit_price: Decimal
    discount_price: Decimal | None = None
    extras: list[CartItemExtraResponse] = Field(default_factory=list)
    line_total: Decimal
    preparation_time_minutes: int | None = None


class OrderSummaryResponse(BaseModel):
    currency: str
    products: list[OrderSummaryLineResponse]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    delivery_fee: Decimal
    grand_total: Decimal
    coupon_code: str | None = None
    estimated_preparation_time_minutes: int
    estimated_delivery_time_minutes: int
    item_count: int


class CheckoutValidationIssue(BaseModel):
    code: str
    message: str
    field: str | None = None


class CheckoutValidationResponse(BaseModel):
    is_valid: bool
    issues: list[CheckoutValidationIssue] = Field(default_factory=list)
    summary: OrderSummaryResponse | None = None
    has_default_address: bool = False
    address_count: int = 0


class CouponValidationResponse(BaseModel):
    code: str
    coupon_type: CouponType
    value: Decimal
    discount_amount: Decimal
    is_valid: bool
    message: str


class WishlistItemResponse(BaseModel):
    product_id: UUID
    product_name: str | None = None
    product_slug: str | None = None
    image_url: str | None = None
    base_price: Decimal | None = None
    is_available: bool | None = None
    added_at: datetime

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    id: UUID
    item_count: int
    items: list[WishlistItemResponse] = Field(default_factory=list)
