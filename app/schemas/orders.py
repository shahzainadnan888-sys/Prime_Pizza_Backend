"""Order and checkout request / response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.common.enums import OrderStatus, PaymentMethod, PaymentStatus


class PlaceOrderRequest(BaseModel):
    address_id: UUID | None = None
    payment_method: PaymentMethod = PaymentMethod.CASH_ON_DELIVERY
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=64)
    # Optional live GPS from the customer device during checkout.
    latitude: Decimal | None = Field(default=None, ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal | None = Field(default=None, ge=Decimal("-180"), le=Decimal("180"))
    gps_accuracy: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="GPS accuracy in meters, when reported by the device",
    )

    @model_validator(mode="after")
    def gps_pair_consistency(self) -> PlaceOrderRequest:
        has_lat = self.latitude is not None
        has_lng = self.longitude is not None
        if has_lat != has_lng:
            raise ValueError("latitude and longitude must be provided together")
        if self.gps_accuracy is not None and not (has_lat and has_lng):
            raise ValueError("gps_accuracy requires latitude and longitude")
        return self



class CancelOrderRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
    notes: str | None = Field(default=None, max_length=1000)


class UpdatePaymentStatusRequest(BaseModel):
    payment_status: PaymentStatus
    notes: str | None = Field(default=None, max_length=1000)


class UpdateOrderNotesRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    kitchen_notes: str | None = Field(default=None, max_length=2000)
    internal_notes: str | None = Field(default=None, max_length=2000)


class OrderFilterParams(BaseModel):
    status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    sort: str = Field(default="newest", pattern="^(newest|oldest)$")
    q: str | None = Field(default=None, max_length=80)
    user_id: UUID | None = None


class OrderItemExtraResponse(BaseModel):
    option_id: UUID | None = None
    option_name: str
    option_type: str | None = None
    quantity: int
    unit_price: Decimal

    model_config = {"from_attributes": True}


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID | None = None
    product_name: str
    product_slug: str | None = None
    variant_id: UUID | None = None
    variant_name: str | None = None
    variant_size: str | None = None
    image_url: str | None = None
    quantity: int
    unit_price: Decimal
    discount_price: Decimal | None = None
    subtotal: Decimal
    preparation_time_minutes: int | None = None
    notes: str | None = None
    extras: list[OrderItemExtraResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OrderTimelineEventResponse(BaseModel):
    id: UUID
    status: OrderStatus
    title: str
    notes: str | None = None
    performed_by: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListItemResponse(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    grand_total: Decimal
    currency: str
    item_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    id: UUID
    order_number: str
    user_id: UUID
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    currency: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    delivery_fee: Decimal
    grand_total: Decimal
    coupon_code: str | None = None
    notes: str | None = None
    kitchen_notes: str | None = None
    internal_notes: str | None = None
    delivery_address_snapshot: dict | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    gps_accuracy: Decimal | None = None
    estimated_preparation_minutes: int | None = None
    estimated_delivery_time: datetime | None = None
    items: list[OrderItemResponse] = Field(default_factory=list)
    timeline: list[OrderTimelineEventResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderTrackingResponse(BaseModel):
    order_id: UUID
    order_number: str
    current_status: OrderStatus
    payment_status: PaymentStatus
    timeline: list[OrderTimelineEventResponse]
    estimated_preparation_minutes: int | None = None
    estimated_delivery_time: datetime | None = None
    last_updated: datetime
