"""Order models with historical line-item snapshots and timeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import OrderStatus, PaymentMethod, PaymentStatus
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.coupon import Coupon, CouponUsage
    from app.models.user import Address, User


class Order(BaseModel):
    """Customer order with financial totals and fulfillment state."""

    __tablename__ = "orders"
    __table_args__ = (
        Index(
            "uq_orders_order_number_active",
            "order_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_payment_status", "payment_status"),
        Index("ix_orders_created_at", "created_at"),
        Index(
            "ix_orders_user_created",
            "user_id",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_orders_status_created",
            "status",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        CheckConstraint("tax >= 0", name="ck_orders_tax_non_negative"),
        CheckConstraint("delivery_fee >= 0", name="ck_orders_delivery_fee_non_negative"),
        CheckConstraint("discount >= 0", name="ck_orders_discount_non_negative"),
        CheckConstraint("grand_total >= 0", name="ck_orders_grand_total_non_negative"),
    )

    order_number: Mapped[str] = mapped_column(String(40), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_address_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        pg_enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR", server_default="PKR")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        pg_enum(PaymentMethod, name="payment_method"),
        nullable=False,
        default=PaymentMethod.CASH_ON_DELIVERY,
        server_default=PaymentMethod.CASH_ON_DELIVERY.value,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_preparation_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_delivery_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
    )
    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped[User] = relationship(back_populates="orders")
    address: Mapped[Address | None] = relationship()
    coupon: Mapped[Coupon | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    timeline: Mapped[list[OrderTimelineEvent]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OrderTimelineEvent.created_at",
    )
    coupon_usages: Mapped[list[CouponUsage]] = relationship(
        back_populates="order",
        passive_deletes=True,
    )


class OrderItem(BaseModel):
    """Order line with a full product snapshot for historical integrity."""

    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
        CheckConstraint("quantity >= 1", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint(
            "discount_price IS NULL OR discount_price >= 0",
            name="ck_order_items_discount_price_non_negative",
        ),
        CheckConstraint("subtotal >= 0", name="ck_order_items_subtotal_non_negative"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_slug: Mapped[str | None] = mapped_column(String(220), nullable=True)
    variant_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    variant_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    preparation_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extras_snapshot: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    product_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped[Order] = relationship(back_populates="items")
    extras: Mapped[list[OrderItemExtra]] = relationship(
        back_populates="order_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderItemExtra(BaseModel):
    """Historical snapshot of extras selected on an order line."""

    __tablename__ = "order_item_extras"
    __table_args__ = (
        Index("ix_order_item_extras_order_item_id", "order_item_id"),
        CheckConstraint("quantity >= 1", name="ck_order_item_extras_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_extras_unit_price_non_negative"),
    )

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variant_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    option_name: Mapped[str] = mapped_column(String(150), nullable=False)
    option_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order_item: Mapped[OrderItem] = relationship(back_populates="extras")


class OrderTimelineEvent(BaseModel):
    """Immutable-ish status timeline for an order."""

    __tablename__ = "order_timeline_events"
    __table_args__ = (
        Index("ix_order_timeline_events_order_id", "order_id"),
        Index("ix_order_timeline_events_created_at", "created_at"),
        Index("ix_order_timeline_events_status", "status"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        pg_enum(OrderStatus, name="order_status", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="timeline")


class OrderNumberSequence(BaseModel):
    """Per-year sequential counter for PP-YYYY-###### numbers."""

    __tablename__ = "order_number_sequences"
    __table_args__ = (Index("uq_order_number_sequences_year", "year", unique=True),)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
