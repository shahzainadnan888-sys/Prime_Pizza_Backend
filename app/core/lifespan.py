"""Application lifespan: startup and shutdown hooks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config.settings import Settings
from app.database.session import close_db, init_db
from app.integrations.cloudinary.client import close_cloudinary, init_cloudinary
from app.integrations.redis.client import close_redis, init_redis
from app.integrations.resend.client import close_resend, init_resend


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage shared resources for the application lifetime."""
    settings: Settings = app.state.settings

    logger.info("Starting {} | env={}", settings.app_name, settings.app_env)

    await init_db(settings)
    await init_redis(settings)
    init_cloudinary(settings)
    init_resend(settings)

    logger.info("All foundational services initialized | otp_provider=local")
    yield

    logger.info("Shutting down {}", settings.app_name)
    await close_redis()
    await close_db()
    close_cloudinary()
    close_resend()
    logger.info("Shutdown complete")
