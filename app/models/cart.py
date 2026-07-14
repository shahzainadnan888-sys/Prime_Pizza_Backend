"""Shopping cart models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.common.enums import CartStatus
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.catalog import Product, ProductVariant, VariantOption
    from app.models.coupon import Coupon
    from app.models.user import User


class Cart(BaseModel):
    """One active cart per customer."""

    __tablename__ = "carts"
    __table_args__ = (
        Index(
            "uq_carts_user_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND is_active IS TRUE"),
        ),
        Index("ix_carts_user_id", "user_id"),
        Index("ix_carts_status", "status"),
        Index("ix_carts_coupon_id", "coupon_id"),
        CheckConstraint("subtotal >= 0", name="ck_carts_subtotal_non_negative"),
        CheckConstraint("discount >= 0", name="ck_carts_discount_non_negative"),
        CheckConstraint("delivery_fee >= 0", name="ck_carts_delivery_fee_non_negative"),
        CheckConstraint("tax >= 0", name="ck_carts_tax_non_negative"),
        CheckConstraint("grand_total >= 0", name="ck_carts_grand_total_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    status: Mapped[CartStatus] = mapped_column(
        pg_enum(CartStatus, name="cart_status"),
        nullable=False,
        default=CartStatus.ACTIVE,
        server_default=CartStatus.ACTIVE.value,
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR", server_default="PKR")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Snapshot totals — always recalculated from PostgreSQL catalog prices.
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    user: Mapped[User] = relationship(back_populates="cart")
    coupon: Mapped[Coupon | None] = relationship()
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CartItem(BaseModel):
    """Line item inside a cart."""

    __tablename__ = "cart_items"
    __table_args__ = (
        Index("ix_cart_items_cart_id", "cart_id"),
        Index("ix_cart_items_product_id", "product_id"),
        Index("ix_cart_items_variant_id", "variant_id"),
        CheckConstraint("quantity >= 1", name="ck_cart_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_cart_items_unit_price_non_negative"),
        CheckConstraint(
            "discount_price IS NULL OR discount_price >= 0",
            name="ck_cart_items_discount_price_non_negative",
        ),
        CheckConstraint("subtotal >= 0", name="ck_cart_items_subtotal_non_negative"),
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    extras_snapshot: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    special_instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)

    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
    variant: Mapped[ProductVariant | None] = relationship()
    extras: Mapped[list[CartItemExtra]] = relationship(
        back_populates="cart_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CartItemExtra(BaseModel):
    """Selected topping / sauce / crust extras for a cart line."""

    __tablename__ = "cart_item_extras"
    __table_args__ = (
        Index(
            "uq_cart_item_extras_item_option_active",
            "cart_item_id",
            "option_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_cart_item_extras_cart_item_id", "cart_item_id"),
        Index("ix_cart_item_extras_option_id", "option_id"),
        CheckConstraint("quantity >= 1", name="ck_cart_item_extras_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_cart_item_extras_unit_price_non_negative"),
    )

    cart_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cart_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variant_options.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    cart_item: Mapped[CartItem] = relationship(back_populates="extras")
    option: Mapped[VariantOption] = relationship()
