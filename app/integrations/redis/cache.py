"""Redis caching layer for catalog and auth helpers."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from redis.asyncio import Redis


class CacheService:
    """Thin Redis cache facade used by catalog and auth modules."""

    def __init__(self, redis: Redis, *, default_ttl_seconds: int = 300) -> None:
        self._redis = redis
        self._default_ttl = default_ttl_seconds

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> bool:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        result = await self._redis.set(key, value, ex=ttl)
        return bool(result)

    async def set_nx(self, key: str, value: str, *, ttl_seconds: int) -> bool:
        """Set key only if it does not already exist (distributed lock helper)."""
        result = await self._redis.set(key, value, nx=True, ex=ttl_seconds)
        return bool(result)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in cache key={}", key)
            return None

    async def set_json(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> bool:
        return await self.set(key, json.dumps(value, default=str), ttl_seconds=ttl_seconds)

    async def delete(self, key: str) -> int:
        return int(await self._redis.delete(key))

    async def delete_prefix(self, prefix: str) -> int:
        """Delete keys matching prefix* via SCAN + batched UNLINK/DELETE."""
        deleted = 0
        batch: list[str] = []
        async for key in self._redis.scan_iter(match=f"{prefix}*", count=200):
            batch.append(key)
            if len(batch) >= 100:
                deleted += int(await self._redis.unlink(*batch))
                batch.clear()
        if batch:
            deleted += int(await self._redis.unlink(*batch))
        return deleted

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def increment_rate_limit(self, key: str, *, window_seconds: int = 60) -> int:
        pipe = self._redis.pipeline()
        rate_key = f"rate:{key}"
        await pipe.incr(rate_key)
        await pipe.expire(rate_key, window_seconds, nx=True)
        results: list[Any] = await pipe.execute()
        return int(results[0])

    async def set_session(self, session_id: str, payload: str, *, ttl_seconds: int) -> bool:
        return await self.set(f"session:{session_id}", payload, ttl_seconds=ttl_seconds)
