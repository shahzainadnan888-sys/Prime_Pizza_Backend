"""Notification and user preference models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import NotificationType
from app.database.types import pg_enum
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Notification(BaseModel):
    """In-app notification record."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_notification_type", "notification_type"),
        Index("ix_notifications_created_at", "created_at"),
        Index(
            "ix_notifications_user_created",
            "user_id",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    notification_type: Mapped[NotificationType] = mapped_column(
        pg_enum(NotificationType, name="notification_type"),
        nullable=False,
        default=NotificationType.SYSTEM,
        server_default=NotificationType.SYSTEM.value,
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="notifications")


class UserPreference(BaseModel):
    """Per-user preferences (UI, locale, and notification channels)."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        Index(
            "uq_user_preferences_user_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dark_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", server_default="en")
    marketing_emails: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    marketing_sms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    push_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    order_updates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    promotional_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    preferred_currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="PKR",
        server_default="PKR",
    )
    preferred_timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Karachi",
        server_default="Asia/Karachi",
    )

    user: Mapped[User] = relationship(back_populates="preferences")


# Backward-compatible alias
NotificationPreference = UserPreference
