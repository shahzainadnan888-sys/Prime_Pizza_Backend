"""Health check response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.common.enums import HealthStatus


class ComponentHealth(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    success: bool = True
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
