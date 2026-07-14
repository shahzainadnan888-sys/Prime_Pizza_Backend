"""Runtime commerce configuration resolved from DB settings with env fallback."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.integrations.redis.cache import CacheService
from app.repositories.system_setting import SystemSettingRepository
from app.services.base import BaseService
from app.services.pricing import money

COMMERCE_CACHE_KEY = "settings:commerce"
COMMERCE_CACHE_TTL_SECONDS = 60


@dataclass(frozen=True)
class CommerceConfig:
    delivery_fee: Decimal
    free_delivery_threshold: Decimal
    tax_percent: Decimal
    maintenance_mode: bool


class CommerceConfigService(BaseService):
    """
    Effective delivery / tax / maintenance values.

    Owner-editable ``system_settings`` keys override env defaults. Results are
    cached briefly in Redis and invalidated whenever settings change.
    """

    service_name = "commerce_config"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        cache: CacheService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._cache = cache
        self._repo = SystemSettingRepository(session)

    def _from_env(self) -> CommerceConfig:
        return CommerceConfig(
            delivery_fee=money(self._settings.delivery_fee_flat),
            free_delivery_threshold=money(self._settings.free_delivery_threshold),
            tax_percent=Decimal(str(self._settings.tax_rate_percent)),
            maintenance_mode=False,
        )

    @staticmethod
    def _parse_decimal(raw: str | None, fallback: Decimal) -> Decimal:
        if raw is None or not str(raw).strip():
            return fallback
        try:
            return money(Decimal(str(raw).strip()))
        except (InvalidOperation, ValueError):
            return fallback

    @staticmethod
    def _parse_bool(raw: str | None) -> bool:
        return (raw or "false").strip().lower() in {"1", "true", "yes", "on"}

    async def get(self) -> CommerceConfig:
        cached = await self._cache.get_json(COMMERCE_CACHE_KEY)
        if isinstance(cached, dict):
            try:
                return CommerceConfig(
                    delivery_fee=money(cached["delivery_fee"]),
                    free_delivery_threshold=money(cached["free_delivery_threshold"]),
                    tax_percent=Decimal(str(cached["tax_percent"])),
                    maintenance_mode=bool(cached.get("maintenance_mode", False)),
                )
            except Exception:
                logger.warning("Invalid commerce config cache payload; refreshing")

        env = self._from_env()
        fee_row = await self._repo.get_by_key("delivery.fee")
        threshold_row = await self._repo.get_by_key("delivery.free_threshold")
        tax_row = await self._repo.get_by_key("tax.percent")
        maintenance_row = await self._repo.get_by_key("maintenance.mode")

        config = CommerceConfig(
            delivery_fee=self._parse_decimal(fee_row.value if fee_row else None, env.delivery_fee),
            free_delivery_threshold=self._parse_decimal(
                threshold_row.value if threshold_row else None,
                env.free_delivery_threshold,
            ),
            tax_percent=self._parse_decimal(
                tax_row.value if tax_row else None,
                env.tax_percent,
            ),
            maintenance_mode=self._parse_bool(maintenance_row.value if maintenance_row else None),
        )
        await self._cache.set_json(
            COMMERCE_CACHE_KEY,
            {
                "delivery_fee": str(config.delivery_fee),
                "free_delivery_threshold": str(config.free_delivery_threshold),
                "tax_percent": str(config.tax_percent),
                "maintenance_mode": config.maintenance_mode,
            },
            ttl_seconds=COMMERCE_CACHE_TTL_SECONDS,
        )
        return config

    @staticmethod
    async def invalidate(cache: CacheService) -> None:
        await cache.delete(COMMERCE_CACHE_KEY)
        await cache.delete("settings:maintenance")
