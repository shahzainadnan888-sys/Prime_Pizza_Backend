"""Bulk catalog and reorder operations for owner dashboard."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBulkIdsRequest(BaseModel):
    product_ids: list[UUID] = Field(..., min_length=1, max_length=200)


class ProductBulkVisibilityRequest(ProductBulkIdsRequest):
    is_visible: bool


class ProductBulkFeaturedRequest(ProductBulkIdsRequest):
    is_featured: bool


class ProductBulkAvailabilityRequest(ProductBulkIdsRequest):
    is_available: bool


class ProductBulkCategoryRequest(ProductBulkIdsRequest):
    category_id: UUID


class ProductBulkDeleteRequest(ProductBulkIdsRequest):
    pass


class BulkMutationResult(BaseModel):
    matched: int
    updated: int


class CategoryReorderItem(BaseModel):
    category_id: UUID
    display_order: int = Field(..., ge=0)


class CategoryReorderRequest(BaseModel):
    items: list[CategoryReorderItem] = Field(..., min_length=1, max_length=200)


class DealScheduleRequest(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None
    is_visible: bool | None = None
