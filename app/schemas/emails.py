"""Email API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import EmailDeliveryStatus, EmailTemplateKey


class TestEmailRequest(BaseModel):
    to: EmailStr | None = Field(
        default=None,
        description="Optional override recipient; defaults to OWNER_EMAIL",
    )
    message: str | None = Field(default=None, max_length=500)


class TestEmailResponse(BaseModel):
    queued: bool
    recipients: list[str]
    subject: str
    status: EmailDeliveryStatus
    email_log_id: UUID | None = None
    detail: str


class EmailLogResponse(BaseModel):
    id: UUID
    recipient: str
    subject: str
    template_key: EmailTemplateKey
    status: EmailDeliveryStatus
    retry_count: int
    failure_reason: str | None = None
    provider_message_id: str | None = None
    sent_at: datetime | None = None
    order_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
