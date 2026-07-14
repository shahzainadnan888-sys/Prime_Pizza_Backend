"""Admin notification management schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.enums import NotificationType


class NotificationCreateRequest(BaseModel):
    user_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    notification_type: NotificationType = NotificationType.SYSTEM
    payload: dict[str, Any] | None = None
    scheduled_at: datetime | None = Field(
        default=None,
        description="Preparation only — stored in payload until a scheduler ships",
    )


class NotificationBroadcastRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    notification_type: NotificationType = NotificationType.SYSTEM
    payload: dict[str, Any] | None = None
    role_filter: str | None = Field(default="customer", pattern="^(customer|owner|all)$")
    scheduled_at: datetime | None = None


class AdminNotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    is_read: bool
    notification_type: NotificationType
    payload: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationBroadcastResult(BaseModel):
    created_count: int
    scheduled: bool = False
