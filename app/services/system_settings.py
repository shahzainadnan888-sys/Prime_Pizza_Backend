"""System settings service for restaurant configuration."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction
from app.config.settings import Settings
from app.core.exceptions import NotFoundException, ValidationException
from app.integrations.redis.cache import CacheService
from app.models.system_setting import SystemSetting
from app.repositories.system_setting import SystemSettingRepository
from app.schemas.admin_settings import (
    RestaurantSettingsResponse,
    SystemSettingResponse,
    SystemSettingsBulkUpdateRequest,
    SystemSettingUpsertRequest,
)
from app.services.audit import AuditService
from app.services.base import BaseService
from app.services.commerce_config import CommerceConfigService
from app.services.dashboard_cache import DashboardCacheService

KNOWN_KEYS: dict[str, dict[str, Any]] = {
    "restaurant.name": {"description": "Restaurant display name", "is_public": True},
    "restaurant.phone": {"description": "Restaurant phone", "is_public": True},
    "restaurant.email": {"description": "Restaurant email", "is_public": True},
    "restaurant.address": {"description": "Restaurant address", "is_public": True},
    "business.hours": {"description": "Business hours JSON", "is_public": True},
    "delivery.fee": {"description": "Default delivery fee", "is_public": True},
    "delivery.free_threshold": {"description": "Free delivery threshold", "is_public": True},
    "tax.percent": {"description": "Tax percentage", "is_public": True},
    "currency": {"description": "Store currency", "is_public": True},
    "theme.settings": {"description": "Theme configuration", "is_public": False},
    "maintenance.mode": {"description": "Maintenance mode flag", "is_public": True},
    "payment.settings": {"description": "Future payment provider settings", "is_public": False},
}


class SystemSettingsService(BaseService):
    service_name = "system_settings"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        audit: AuditService,
        dashboard_cache: DashboardCacheService,
        cache: CacheService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repo = SystemSettingRepository(session)
        self._audit = audit
        self._dashboard_cache = dashboard_cache
        self._cache = cache

    def _defaults(self) -> dict[str, tuple[str | None, dict | list | None]]:
        return {
            "restaurant.name": (self._settings.email_brand_name, None),
            "restaurant.phone": (self._settings.owner_phone_number, None),
            "restaurant.email": (str(self._settings.owner_email), None),
            "restaurant.address": (None, None),
            "business.hours": (None, {"monday": "11:00-23:00"}),
            "delivery.fee": (str(self._settings.delivery_fee_flat), None),
            "delivery.free_threshold": (str(self._settings.free_delivery_threshold), None),
            "tax.percent": (str(self._settings.tax_rate_percent), None),
            "currency": ("PKR", None),
            "theme.settings": (None, {"primary": "#C41E3A"}),
            "maintenance.mode": ("false", None),
            "payment.settings": (None, {"online_enabled": False}),
        }

    async def ensure_defaults(self) -> None:
        defaults = self._defaults()
        for key, meta in KNOWN_KEYS.items():
            existing = await self._repo.get_by_key(key)
            if existing is not None:
                continue
            value, value_json = defaults.get(key, (None, None))
            await self._repo.add(
                SystemSetting(
                    key=key,
                    value=value,
                    value_json=value_json,
                    description=meta["description"],
                    is_public=bool(meta["is_public"]),
                )
            )
        await self._session.commit()

    async def list_settings(self) -> list[SystemSettingResponse]:
        await self.ensure_defaults()
        rows = await self._repo.list_all_settings()
        return [SystemSettingResponse.model_validate(row) for row in rows]

    async def get_setting(self, key: str) -> SystemSettingResponse:
        await self.ensure_defaults()
        row = await self._repo.get_by_key(key)
        if row is None:
            raise NotFoundException("Setting not found")
        return SystemSettingResponse.model_validate(row)

    async def upsert(
        self,
        key: str,
        payload: SystemSettingUpsertRequest,
        *,
        actor_id: UUID,
    ) -> SystemSettingResponse:
        if key not in KNOWN_KEYS and not key.startswith(
            (
                "restaurant.",
                "business.",
                "delivery.",
                "tax.",
                "theme.",
                "payment.",
                "currency",
                "maintenance.",
            )
        ):
            raise ValidationException("Unknown settings key")
        row = await self._repo.get_by_key(key)
        if row is None:
            meta = KNOWN_KEYS.get(key, {"description": None, "is_public": False})
            row = SystemSetting(
                key=key,
                value=payload.value,
                value_json=payload.value_json,
                description=payload.description or meta.get("description"),
                is_public=payload.is_public if payload.is_public is not None else bool(meta.get("is_public")),
                created_by=actor_id,
            )
            await self._repo.add(row)
        else:
            if payload.value is not None:
                row.value = payload.value
            if payload.value_json is not None:
                row.value_json = payload.value_json
            if payload.description is not None:
                row.description = payload.description
            if payload.is_public is not None:
                row.is_public = payload.is_public
            row.updated_by = actor_id
        await self._session.commit()
        await self._session.refresh(row)
        await self._audit.record(
            action=AuditAction.UPDATE,
            resource_type="system_setting",
            resource_id=key,
            user_id=actor_id,
            message="Settings updated",
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        await CommerceConfigService.invalidate(self._cache)
        if key == "maintenance.mode":
            enabled = (row.value or "").strip().lower() in {"1", "true", "yes", "on"}
            await self._cache.set(
                "settings:maintenance",
                "true" if enabled else "false",
                ttl_seconds=300,
            )
        logger.info("Settings updated | key={}", key)
        return SystemSettingResponse.model_validate(row)

    async def bulk_upsert(
        self,
        payload: SystemSettingsBulkUpdateRequest,
        *,
        actor_id: UUID,
    ) -> list[SystemSettingResponse]:
        results = []
        for key, item in payload.settings.items():
            results.append(await self.upsert(key, item, actor_id=actor_id))
        return results

    async def restaurant_view(self) -> RestaurantSettingsResponse:
        rows = {item.key: item for item in await self.list_settings()}

        def text(key: str) -> str | None:
            row = rows.get(key)
            return row.value if row else None

        def json_val(key: str):
            row = rows.get(key)
            return row.value_json if row else None

        maintenance = (text("maintenance.mode") or "false").lower() in {"1", "true", "yes"}
        return RestaurantSettingsResponse(
            restaurant_name=text("restaurant.name"),
            restaurant_phone=text("restaurant.phone"),
            restaurant_email=text("restaurant.email"),
            restaurant_address=text("restaurant.address"),
            business_hours=json_val("business.hours"),
            delivery_fee=text("delivery.fee"),
            free_delivery_threshold=text("delivery.free_threshold"),
            tax_percentage=text("tax.percent"),
            currency=text("currency"),
            theme_settings=json_val("theme.settings"),
            maintenance_mode=maintenance,
            payment_settings=json_val("payment.settings"),
        )
