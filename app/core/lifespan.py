"""Application lifespan: startup and shutdown hooks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config.settings import Settings
from app.database.session import async_session_factory, close_db, init_db
from app.integrations.brevo.client import close_brevo, init_brevo
from app.integrations.cloudinary.client import close_cloudinary, init_cloudinary
from app.integrations.redis.client import close_redis, get_redis, init_redis
from app.services.bootstrap import (
    ensure_chef_account,
    ensure_demo_catalog,
    ensure_demo_coupons,
    ensure_schema_ready,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage shared resources for the application lifetime."""
    settings: Settings = app.state.settings

    logger.info("Starting {} | env={}", settings.app_name, settings.app_env)

    await init_db(settings)
    await ensure_schema_ready(settings)
    await init_redis(settings)
    init_cloudinary(settings)
    settings.validate_brevo_required()
    init_brevo(settings, strict=settings.email_enabled and settings.app_env != "test")

    session_factory = async_session_factory()
    redis = get_redis()
    await ensure_chef_account(
        session_factory=session_factory,
        redis=redis,
        settings=settings,
    )
    await ensure_demo_catalog(session_factory=session_factory)
    await ensure_demo_coupons(session_factory=session_factory)

    logger.info("All foundational services initialized")
    yield

    logger.info("Shutting down {}", settings.app_name)
    await close_redis()
    await close_db()
    close_cloudinary()
    close_brevo()
    logger.info("Shutdown complete")
