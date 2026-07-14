"""Enterprise admin search schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SearchEntity = Literal[
    "customers",
    "orders",
    "products",
    "coupons",
    "deals",
    "categories",
    "audit_logs",
]


class AdminSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=200)
    entities: list[SearchEntity] | None = None
    limit_per_entity: int = Field(default=10, ge=1, le=50)


class AdminSearchHit(BaseModel):
    entity: SearchEntity
    id: str
    title: str
    subtitle: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class AdminSearchResponse(BaseModel):
    query: str
    results: list[AdminSearchHit]
    total_hits: int
