"""Pagination computation helpers."""

from __future__ import annotations

from app.schemas.pagination import PaginationMeta, PaginationParams


def build_pagination_meta(params: PaginationParams, total_items: int) -> PaginationMeta:
    """Build pagination metadata from params + total count."""
    return PaginationMeta.from_totals(
        page=params.page,
        page_size=params.page_size,
        total_items=total_items,
    )
