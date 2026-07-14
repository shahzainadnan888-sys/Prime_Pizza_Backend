"""Response construction helpers."""

from __future__ import annotations

from typing import Any

from app.common.constants import APIMessages
from app.schemas.pagination import PaginationMeta
from app.schemas.response import MessageResponse, PaginatedResponse, SuccessResponse


def success_response[T](
    data: T | None = None,
    *,
    message: str = APIMessages.SUCCESS,
    meta: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> SuccessResponse[T]:
    return SuccessResponse(
        success=True,
        message=message,
        data=data,
        meta=meta,
        request_id=request_id,
    )


def message_response(
    message: str,
    *,
    request_id: str | None = None,
) -> MessageResponse:
    return MessageResponse(success=True, message=message, request_id=request_id)


def paginated_response[T](
    items: list[T],
    *,
    pagination: PaginationMeta,
    message: str = APIMessages.SUCCESS,
    request_id: str | None = None,
) -> PaginatedResponse[T]:
    return PaginatedResponse(
        success=True,
        message=message,
        data=items,
        meta=pagination.model_dump(),
        request_id=request_id,
    )
