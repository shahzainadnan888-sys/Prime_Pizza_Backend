"""User and address models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import UserRole
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.cart import Cart
    from app.models.coupon import CouponUsage
    from app.models.notification import Notification, UserPreference
    from app.models.order import Order
    from app.models.wishlist import Wishlist


class User(BaseModel):
    """Platform user (customer or chef)."""

    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_users_phone_active",
            "phone_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND phone_number IS NOT NULL"),
        ),
        Index(
            "uq_users_email_active",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
        Index("ix_users_full_name", "full_name"),
    )

    first_name: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    last_name: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.CUSTOMER,
        server_default=UserRole.CUSTOMER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    addresses: Mapped[list[Address]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cart: Mapped[Cart | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    wishlist: Mapped[Wishlist | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    orders: Mapped[list[Order]] = relationship(back_populates="user", passive_deletes=True)
    coupon_usages: Mapped[list[CouponUsage]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    preferences: Mapped[UserPreference | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="user", passive_deletes=True)

    @property
    def notification_preference(self) -> UserPreference | None:
        return self.preferences


class Address(BaseModel):
    """Customer delivery address (many per user)."""

    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_user_id", "user_id"),
        Index(
            "uq_addresses_default_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND is_default IS TRUE"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False, server_default="")
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[str | None] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Pakistan",
        server_default="Pakistan",
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    delivery_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="addresses")
