"""Redis connection manager and dependency helpers."""

from __future__ import annotations

from loguru import logger
from redis.asyncio import Redis

from app.config.settings import Settings

_redis_client: Redis | None = None


async def init_redis(settings: Settings) -> None:
    """Initialize the shared async Redis client."""
    global _redis_client

    _redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_timeout=5,
        max_connections=settings.redis_max_connections,
    )
    # Validate connectivity early so startup fails fast on misconfiguration.
    await _redis_client.ping()
    logger.info("Redis client initialized")


async def close_redis() -> None:
    """Close the shared Redis client."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        logger.info("Redis client closed")
    _redis_client = None


def get_redis() -> Redis:
    """Return the initialized Redis client."""
    if _redis_client is None:
        msg = "Redis client is not initialized. Call init_redis() during startup."
        raise RuntimeError(msg)
    return _redis_client


async def redis_ping() -> bool:
    """Return True when Redis responds to PING."""
    client = get_redis()
    result = await client.ping()
    return bool(result)
