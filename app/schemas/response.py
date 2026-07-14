"""Standard API response envelopes used by every endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error payload."""

    code: str
    details: Any | None = None


class SuccessResponse[T](BaseModel):
    """Standard success envelope."""

    success: bool = True
    message: str = "Success"
    data: T | None = None
    meta: dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: bool = False
    message: str
    error: ErrorDetail
    request_id: str | None = None
    status_code: int | None = None


class MessageResponse(BaseModel):
    """Simple message-only success envelope."""

    success: bool = True
    message: str
    request_id: str | None = None


class PaginatedResponse[T](BaseModel):
    """Paginated success envelope."""

    success: bool = True
    message: str = "Success"
    data: list[T] = Field(default_factory=list)
    meta: dict[str, Any]
    request_id: str | None = None
