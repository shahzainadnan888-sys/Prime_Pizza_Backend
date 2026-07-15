"""Typed payloads for transactional email rendering and delivery."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.common.enums import EmailTemplateKey


@dataclass(slots=True)
class OrderEmailLineExtra:
    name: str
    quantity: int
    unit_price: Decimal


@dataclass(slots=True)
class OrderEmailLineItem:
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    variant_name: str | None = None
    image_url: str | None = None
    extras: list[OrderEmailLineExtra] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class OrderEmailPayload:
    """Serializable order snapshot used after commit for order emails."""

    order_id: UUID
    order_number: str
    order_created_at: datetime
    customer_name: str
    customer_phone: str | None
    customer_email: str | None
    delivery_address: str
    payment_method: str
    payment_status: str
    order_status: str
    currency: str
    subtotal: Decimal
    delivery_fee: Decimal
    tax: Decimal
    discount: Decimal
    grand_total: Decimal
    customer_notes: str | None
    estimated_preparation_minutes: int | None
    items: list[OrderEmailLineItem]
    brand_name: str = "Prime Pizza"
    logo_url: str | None = None
    estimated_delivery_time: datetime | None = None


@dataclass(slots=True)
class OwnerTestEmailPayload:
    brand_name: str = "Prime Pizza"
    logo_url: str | None = None
    message: str = "This is a Prime Pizza transactional email connectivity test."


@dataclass(slots=True)
class AttachmentPayload:
    """Future attachment support (filename + content bytes or remote path)."""

    filename: str
    content: bytes | None = None
    path: str | None = None
    content_type: str | None = None


@dataclass(slots=True)
class RenderedEmail:
    template_key: EmailTemplateKey
    subject: str
    html: str
    text: str


@dataclass(slots=True)
class EmailMessage:
    """Outbound email envelope prepared for the email service."""

    template_key: EmailTemplateKey
    to: list[str]
    subject: str
    html: str
    text: str
    order_id: UUID | None = None
    attachments: list[AttachmentPayload] = field(default_factory=list)
    tags: list[dict[str, str]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    scheduled_at: str | None = None  # future scheduled email support
