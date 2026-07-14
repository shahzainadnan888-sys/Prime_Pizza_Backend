"""Deal / combo models."""

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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import DealType
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.catalog import Product


class Deal(BaseModel):
    """Combo meals, family deals, and limited / time-based offers."""

    __tablename__ = "deals"
    __table_args__ = (
        Index(
            "uq_deals_slug_active",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_deals_deal_type", "deal_type"),
        Index("ix_deals_is_active", "is_active"),
        Index("ix_deals_is_visible", "is_visible"),
        Index("ix_deals_starts_at", "starts_at"),
        Index("ix_deals_ends_at", "ends_at"),
        CheckConstraint("deal_price >= 0", name="ck_deals_price_non_negative"),
        CheckConstraint(
            "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
            name="ck_deals_discount_percent_range",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at",
            name="ck_deals_ends_after_starts",
        ),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deal_type: Mapped[DealType] = mapped_column(pg_enum(DealType, name="deal_type"), nullable=False)
    deal_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deal_products: Mapped[list[DealProduct]] = relationship(
        back_populates="deal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DealProduct(BaseModel):
    """Products included in a deal (with quantity)."""

    __tablename__ = "deal_products"
    __table_args__ = (
        Index(
            "uq_deal_products_deal_product_active",
            "deal_id",
            "product_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_deal_products_deal_id", "deal_id"),
        Index("ix_deal_products_product_id", "product_id"),
        CheckConstraint("quantity >= 1", name="ck_deal_products_quantity_positive"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    deal: Mapped[Deal] = relationship(back_populates="deal_products")
    product: Mapped[Product] = relationship(back_populates="deal_products")
