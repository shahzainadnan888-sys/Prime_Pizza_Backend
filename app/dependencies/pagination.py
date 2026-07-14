"""Pagination dependency."""

from __future__ import annotations

from fastapi import Query

from app.common.constants import AppConstants
from app.schemas.pagination import PaginationParams


def get_pagination(
    page: int = Query(default=AppConstants.DEFAULT_PAGE, ge=1, description="Page number"),
    page_size: int = Query(
        default=AppConstants.DEFAULT_PAGE_SIZE,
        ge=1,
        le=AppConstants.MAX_PAGE_SIZE,
        description="Items per page",
    ),
) -> PaginationParams:
    """Parse and validate pagination query parameters."""
    return PaginationParams(page=page, page_size=page_size)
