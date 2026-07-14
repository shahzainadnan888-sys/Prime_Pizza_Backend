"""Redis cache for owner dashboard and analytics."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.config.settings import Settings
from app.integrations.redis.cache import CacheService
from app.services.base import BaseService


class DashboardCacheService(BaseService):
    service_name = "dashboard_cache"
    PREFIX = "dashboard"

    def __init__(self, cache: CacheService, settings: Settings) -> None:
        self._cache = cache
        self._ttl = settings.dashboard_cache_ttl_seconds

    def stats_key(self) -> str:
        return f"{self.PREFIX}:stats"

    def analytics_key(self, period: str, fingerprint: str) -> str:
        return f"{self.PREFIX}:analytics:{period}:{fingerprint}"

    def charts_key(self, period: str) -> str:
        return f"{self.PREFIX}:charts:{period}"

    def tops_key(self, kind: str) -> str:
        return f"{self.PREFIX}:tops:{kind}"

    async def get_json(self, key: str) -> Any | None:
        try:
            return await self._cache.get_json(key)
        except Exception:
            logger.exception("Dashboard cache get failed | key={}", key)
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._cache.set_json(key, value, ttl_seconds=self._ttl)
        except Exception:
            logger.exception("Dashboard cache set failed | key={}", key)

    async def invalidate_all(self) -> None:
        try:
            deleted = await self._cache.delete_prefix(f"{self.PREFIX}:")
            self.log_info("Dashboard cache invalidated | deleted={}", deleted)
        except Exception:
            logger.exception("Dashboard cache invalidation failed")
