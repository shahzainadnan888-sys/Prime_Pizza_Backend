"""Coupon models."""

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

from app.common.enums import CouponType
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class Coupon(BaseModel):
    """Discount coupon configuration."""

    __tablename__ = "coupons"
    __table_args__ = (
        Index(
            "uq_coupons_code_active",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_coupons_is_active", "is_active"),
        Index("ix_coupons_expires_at", "expires_at"),
        CheckConstraint("value >= 0", name="ck_coupons_value_non_negative"),
        CheckConstraint(
            "minimum_order_amount IS NULL OR minimum_order_amount >= 0",
            name="ck_coupons_min_order_non_negative",
        ),
        CheckConstraint(
            "maximum_discount IS NULL OR maximum_discount >= 0",
            name="ck_coupons_max_discount_non_negative",
        ),
        CheckConstraint(
            "usage_limit IS NULL OR usage_limit >= 0",
            name="ck_coupons_usage_limit_non_negative",
        ),
        CheckConstraint(
            "per_user_limit IS NULL OR per_user_limit >= 0",
            name="ck_coupons_per_user_limit_non_negative",
        ),
        CheckConstraint(
            "coupon_type <> 'percentage' OR value <= 100",
            name="ck_coupons_percentage_max_100",
        ),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    coupon_type: Mapped[CouponType] = mapped_column(
        pg_enum(CouponType, name="coupon_type"),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    maximum_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_user_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    usages: Mapped[list[CouponUsage]] = relationship(
        back_populates="coupon",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    orders: Mapped[list[Order]] = relationship(back_populates="coupon", passive_deletes=True)


class CouponUsage(BaseModel):
    """Tracks which user applied which coupon on which order."""

    __tablename__ = "coupon_usages"
    __table_args__ = (
        Index(
            "uq_coupon_usages_coupon_order_active",
            "coupon_id",
            "order_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_coupon_usages_user_id", "user_id"),
        Index("ix_coupon_usages_coupon_id", "coupon_id"),
        Index("ix_coupon_usages_order_id", "order_id"),
        Index("ix_coupon_usages_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    coupon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coupons.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    discount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    user: Mapped[User] = relationship(back_populates="coupon_usages")
    coupon: Mapped[Coupon] = relationship(back_populates="usages")
    order: Mapped[Order] = relationship(back_populates="coupon_usages")
