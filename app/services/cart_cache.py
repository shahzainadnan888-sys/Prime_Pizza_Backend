"""Redis cache for cart and checkout summaries."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger

from app.config.settings import Settings
from app.integrations.redis.cache import CacheService
from app.services.base import BaseService


class CartCacheService(BaseService):
    service_name = "cart_cache"
    PREFIX = "cart"

    def __init__(self, cache: CacheService, settings: Settings) -> None:
        self._cache = cache
        self._ttl = settings.cart_cache_ttl_seconds

    def summary_key(self, user_id: UUID) -> str:
        return f"{self.PREFIX}:summary:{user_id}"

    def checkout_key(self, user_id: UUID) -> str:
        return f"{self.PREFIX}:checkout:{user_id}"

    def coupon_key(self, code: str) -> str:
        return f"{self.PREFIX}:coupon:{code.upper()}"

    async def get_json(self, key: str) -> Any | None:
        try:
            return await self._cache.get_json(key)
        except Exception:
            logger.exception("Cart cache get failed | key={}", key)
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._cache.set_json(key, value, ttl_seconds=self._ttl)
        except Exception:
            logger.exception("Cart cache set failed | key={}", key)

    async def invalidate_user(self, user_id: UUID) -> None:
        try:
            await self._cache.delete(self.summary_key(user_id))
            await self._cache.delete(self.checkout_key(user_id))
        except Exception:
            logger.exception("Cart cache invalidate failed | user_id={}", user_id)

    async def invalidate_coupon(self, code: str) -> None:
        try:
            await self._cache.delete(self.coupon_key(code))
        except Exception:
            logger.exception("Coupon cache invalidate failed | code={}", code)
