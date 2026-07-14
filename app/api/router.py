"""Top-level API router registration helpers."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import api_v1_router, health_router
from app.config.settings import Settings


def register_routers(app: FastAPI, settings: Settings) -> None:
    """
    Mount routers.

    - Health probes: `/` and `/api/v1`
    - Auth + future domain APIs: `/api/v1` only
    """
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
