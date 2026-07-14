"""Catalog Redis cache keys and invalidation."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.config.settings import Settings
from app.integrations.redis.cache import CacheService
from app.services.base import BaseService


class CatalogCacheService(BaseService):
    """Cache reads for public catalog surfaces with write-through invalidation."""

    service_name = "catalog_cache"

    PREFIX = "catalog"

    def __init__(self, cache: CacheService, settings: Settings) -> None:
        self._cache = cache
        self._ttl = settings.catalog_cache_ttl_seconds

    def categories_key(self) -> str:
        return f"{self.PREFIX}:categories"

    def featured_key(self) -> str:
        return f"{self.PREFIX}:featured"

    def popular_key(self) -> str:
        return f"{self.PREFIX}:popular"

    def deals_key(self) -> str:
        return f"{self.PREFIX}:deals"

    def product_key(self, slug: str) -> str:
        return f"{self.PREFIX}:product:{slug}"

    def search_key(self, fingerprint: str) -> str:
        return f"{self.PREFIX}:search:{fingerprint}"

    async def get_json(self, key: str) -> Any | None:
        try:
            return await self._cache.get_json(key)
        except Exception:
            logger.exception("Catalog cache get failed | key={}", key)
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._cache.set_json(key, value, ttl_seconds=self._ttl)
        except Exception:
            logger.exception("Catalog cache set failed | key={}", key)

    async def invalidate_all(self) -> None:
        try:
            deleted = await self._cache.delete_prefix(f"{self.PREFIX}:")
            self.log_info("Catalog cache invalidated | deleted={}", deleted)
        except Exception:
            logger.exception("Catalog cache invalidation failed")
