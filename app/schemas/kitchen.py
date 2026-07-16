"""Kitchen dashboard schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator

from app.common.enums import OrderStatus, PaymentStatus


class KitchenOrderItemResponse(BaseModel):
    product_name: str
    variant_name: str | None = None
    quantity: int
    special_instructions: str | None = None


class KitchenOrderCardResponse(BaseModel):
    """Order card shown on the kitchen dashboard boards."""

    id: UUID
    order_number: str
    customer_name: str
    customer_email: str | None = None
    customer_phone: str | None
    items: list[KitchenOrderItemResponse]
    special_instructions: str | None
    notes: str | None = None
    payment_status: PaymentStatus
    payment_method: str | None = None
    delivery_type: str = "delivery"
    order_time: datetime
    status: OrderStatus
    estimated_time: datetime | None
    estimated_preparation_minutes: int | None = None
    grand_total: Decimal | None = None
    address_summary: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    gps_accuracy: float | None = None


class KitchenBoardResponse(BaseModel):
    """All kitchen boards in one payload for polling."""

    incoming: list[KitchenOrderCardResponse] = Field(default_factory=list)
    preparing: list[KitchenOrderCardResponse] = Field(default_factory=list)
    ready: list[KitchenOrderCardResponse] = Field(default_factory=list)
    completed: list[KitchenOrderCardResponse] = Field(default_factory=list)
    cancelled: list[KitchenOrderCardResponse] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pending(self) -> list[KitchenOrderCardResponse]:
        """Alias for frontends that label the first board as pending."""
        return self.incoming


class KitchenActionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class KitchenStatusUpdateRequest(BaseModel):
    """Chef order status update using kitchen vocabulary."""

    status: str = Field(..., min_length=3, max_length=32)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "pending": "pending",
            "incoming": "pending",
            "confirmed": "pending",
            "preparing": "preparing",
            "start_preparing": "preparing",
            "ready": "ready",
            "mark_ready": "ready",
            "completed": "completed",
            "complete": "completed",
            "delivered": "completed",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "cancel": "cancelled",
        }
        mapped = aliases.get(cleaned)
        if mapped is None:
            raise ValueError(
                "status must be one of: pending, preparing, ready, completed"
            )
        return mapped
