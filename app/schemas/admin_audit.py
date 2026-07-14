"""Audit log admin schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.enums import AuditAction


class AuditLogFilterParams(BaseModel):
    q: str | None = Field(default=None, max_length=200)
    user_id: UUID | None = None
    action: AuditAction | None = None
    resource_type: str | None = Field(default=None, max_length=100)
    date_from: datetime | None = None
    date_to: datetime | None = None
    sort: str = Field(default="newest", pattern="^(newest|oldest)$")


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: AuditAction
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    details: dict[str, Any] | None
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
