"""Pagination schemas and helpers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.constants import AppConstants


class PaginationParams(BaseModel):
    """Query parameters for list endpoints."""

    page: int = Field(default=AppConstants.DEFAULT_PAGE, ge=1)
    page_size: int = Field(
        default=AppConstants.DEFAULT_PAGE_SIZE,
        ge=1,
        le=AppConstants.MAX_PAGE_SIZE,
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def from_totals(cls, *, page: int, page_size: int, total_items: int) -> PaginationMeta:
        total_pages = (total_items + page_size - 1) // page_size if page_size else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
