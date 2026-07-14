"""System key-value settings model."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SystemSetting(BaseModel):
    """Application configuration stored as typed key-value pairs."""

    __tablename__ = "system_settings"
    __table_args__ = (
        Index(
            "uq_system_settings_key_active",
            "key",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_system_settings_is_public", "is_public"),
    )

    key: Mapped[str] = mapped_column(String(150), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict[str, Any] | list | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
