"""System settings admin schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SystemSettingResponse(BaseModel):
    id: UUID
    key: str
    value: str | None
    value_json: dict[str, Any] | list[Any] | None
    description: str | None
    is_public: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingUpsertRequest(BaseModel):
    value: str | None = None
    value_json: dict[str, Any] | list[Any] | None = None
    description: str | None = Field(default=None, max_length=2000)
    is_public: bool | None = None


class SystemSettingsBulkUpdateRequest(BaseModel):
    settings: dict[str, SystemSettingUpsertRequest]


class RestaurantSettingsResponse(BaseModel):
    """Typed view of common restaurant settings."""

    restaurant_name: str | None = None
    restaurant_phone: str | None = None
    restaurant_email: str | None = None
    restaurant_address: str | None = None
    business_hours: dict[str, Any] | list[Any] | None = None
    delivery_fee: str | None = None
    free_delivery_threshold: str | None = None
    tax_percentage: str | None = None
    currency: str | None = None
    theme_settings: dict[str, Any] | list[Any] | None = None
    maintenance_mode: bool = False
    payment_settings: dict[str, Any] | list[Any] | None = None
