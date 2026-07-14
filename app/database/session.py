"""SQLAlchemy async engine, session factory, and dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import Settings

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        msg = "Database engine is not initialized. Call init_db() during startup."
        raise RuntimeError(msg)
    return _engine


def async_session_factory() -> async_sessionmaker[AsyncSession]:
    if _async_session_factory is None:
        msg = "Session factory is not initialized. Call init_db() during startup."
        raise RuntimeError(msg)
    return _async_session_factory


async def init_db(settings: Settings) -> None:
    """Create the async engine and session factory."""
    global _engine, _async_session_factory

    connect_args: dict[str, Any] = {}
    # Neon / serverless Postgres often benefits from disabling prepared statements
    # when using transaction poolers.
    if "neon.tech" in settings.database_url:
        connect_args["statement_cache_size"] = 0

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug and settings.is_development,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_timeout=settings.db_pool_timeout_seconds,
        connect_args=connect_args,
    )
    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    logger.info("Database engine initialized")


async def close_db() -> None:
    """Dispose the async engine."""
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
    _engine = None
    _async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped async session.

    Callers / services own commit boundaries. Roll back automatically on error.
    """
    session_factory = async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
