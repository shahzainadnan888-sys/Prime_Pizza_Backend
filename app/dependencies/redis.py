"""Redis dependency providers."""

from __future__ import annotations

from redis.asyncio import Redis

from app.integrations.redis.cache import CacheService
from app.integrations.redis.client import get_redis


def get_redis_client() -> Redis:
    """Provide the shared Redis client."""
    return get_redis()


def get_cache_service() -> CacheService:
    """Provide a Redis-backed cache service instance."""
    return CacheService(get_redis())
