"""Order Redis cache."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger

from app.config.settings import Settings
from app.integrations.redis.cache import CacheService
from app.services.base import BaseService


class OrderCacheService(BaseService):
    service_name = "order_cache"
    PREFIX = "orders"

    def __init__(self, cache: CacheService, settings: Settings) -> None:
        self._cache = cache
        self._ttl = settings.order_cache_ttl_seconds
        self._lock_ttl = settings.checkout_lock_ttl_seconds

    def customer_list_key(self, user_id: UUID) -> str:
        return f"{self.PREFIX}:customer:{user_id}"

    def tracking_key(self, order_id: UUID) -> str:
        return f"{self.PREFIX}:tracking:{order_id}"

    def detail_key(self, order_id: UUID) -> str:
        return f"{self.PREFIX}:detail:{order_id}"

    def recent_key(self) -> str:
        return f"{self.PREFIX}:recent"

    def checkout_lock_key(self, user_id: UUID) -> str:
        return f"{self.PREFIX}:checkout_lock:{user_id}"

    def idempotency_key(self, user_id: UUID, key: str) -> str:
        return f"{self.PREFIX}:idempotency:{user_id}:{key}"

    async def get_json(self, key: str) -> Any | None:
        try:
            return await self._cache.get_json(key)
        except Exception:
            logger.exception("Order cache get failed | key={}", key)
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._cache.set_json(key, value, ttl_seconds=self._ttl)
        except Exception:
            logger.exception("Order cache set failed | key={}", key)

    async def acquire_checkout_lock(self, user_id: UUID) -> bool:
        try:
            return await self._cache.set_nx(
                self.checkout_lock_key(user_id),
                "1",
                ttl_seconds=self._lock_ttl,
            )
        except Exception:
            logger.exception("Checkout lock acquire failed | user_id={}", user_id)
            # Fail closed for write race protection — DB FOR UPDATE remains as backup,
            # but without Redis lock we reject to prevent duplicate submissions.
            return False

    async def release_checkout_lock(self, user_id: UUID) -> None:
        try:
            await self._cache.delete(self.checkout_lock_key(user_id))
        except Exception:
            logger.exception("Checkout lock release failed | user_id={}", user_id)

    async def get_idempotent_order_id(self, user_id: UUID, key: str) -> UUID | None:
        try:
            raw = await self._cache.get(self.idempotency_key(user_id, key))
            return UUID(raw) if raw else None
        except Exception:
            logger.exception("Idempotency get failed | user_id={}", user_id)
            return None

    async def store_idempotent_order_id(self, user_id: UUID, key: str, order_id: UUID) -> None:
        try:
            await self._cache.set(
                self.idempotency_key(user_id, key),
                str(order_id),
                ttl_seconds=max(self._ttl, 86_400),
            )
        except Exception:
            logger.exception("Idempotency store failed | user_id={}", user_id)

    async def invalidate_order(self, *, user_id: UUID, order_id: UUID) -> None:
        try:
            await self._cache.delete(self.customer_list_key(user_id))
            await self._cache.delete(self.tracking_key(order_id))
            await self._cache.delete(self.detail_key(order_id))
            await self._cache.delete(self.recent_key())
        except Exception:
            logger.exception("Order cache invalidate failed | order_id={}", order_id)
