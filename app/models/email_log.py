"""Email delivery log for transactional notifications and future reporting."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import EmailDeliveryStatus, EmailTemplateKey
from app.database.types import pg_enum
from app.models.base import BaseModel


class EmailLog(BaseModel):
    """
    Optional persistence for outbound transactional emails.

    Stores delivery metadata for retries/reporting — never stores HTML bodies
    or secrets to keep the table lean and privacy-safe.
    """

    __tablename__ = "email_logs"
    __table_args__ = (
        Index("ix_email_logs_status", "status"),
        Index("ix_email_logs_template_key", "template_key"),
        Index("ix_email_logs_order_id", "order_id"),
        Index("ix_email_logs_created_at", "created_at"),
        Index("ix_email_logs_recipient", "recipient"),
    )

    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    template_key: Mapped[EmailTemplateKey] = mapped_column(
        pg_enum(EmailTemplateKey, name="email_template_key"),
        nullable=False,
    )
    status: Mapped[EmailDeliveryStatus] = mapped_column(
        pg_enum(EmailDeliveryStatus, name="email_delivery_status"),
        nullable=False,
        default=EmailDeliveryStatus.QUEUED,
        server_default=EmailDeliveryStatus.QUEUED.value,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
