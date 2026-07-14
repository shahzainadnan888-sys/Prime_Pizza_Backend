"""Maintenance-mode gate using cached commerce configuration."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.constants import APIMessages, AppConstants
from app.config.settings import Settings
from app.integrations.redis.client import get_redis
from app.services.commerce_config import COMMERCE_CACHE_KEY

# Paths that remain available during maintenance (probes + owner auth + admin).
_ALLOWED_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)
_ALLOWED_EXACT = {"/", "/favicon.ico"}


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """
    Return 503 when ``maintenance.mode`` is enabled in system settings.

    Fail-open if Redis is unavailable so a cache outage does not brick the API.
    Owner admin routes remain reachable so the flag can be cleared.
    """

    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    def _is_exempt(self, path: str) -> bool:
        if path in _ALLOWED_EXACT:
            return True
        if any(path == p or path.startswith(f"{p}/") for p in _ALLOWED_PREFIXES):
            return True
        lower = path.lower()
        if "/auth/" in lower:
            return True
        return "/admin/" in lower

    async def _maintenance_enabled(self) -> bool:
        try:
            redis = get_redis()
            raw = await redis.get(COMMERCE_CACHE_KEY)
            if raw:
                payload = json.loads(raw)
                return bool(payload.get("maintenance_mode", False))
            flag = await redis.get("settings:maintenance")
            if not flag:
                return False
            value = flag.decode() if isinstance(flag, bytes) else str(flag)
            return value.lower() in {"1", "true", "yes", "on"}
        except Exception:
            logger.debug("Maintenance flag check failed open")
            return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        if not await self._maintenance_enabled():
            return await call_next(request)

        request_id = getattr(request.state, "request_id", None)
        headers: dict[str, str] = {"Retry-After": "300"}
        if request_id:
            headers[AppConstants.REQUEST_ID_HEADER] = str(request_id)
        logger.warning(
            "Security event | type=maintenance_mode | path={} | id={}",
            path,
            request_id,
        )
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": APIMessages.MAINTENANCE,
                "error": {"code": "maintenance_mode", "details": None},
                "request_id": request_id,
                "status_code": 503,
            },
            headers=headers,
        )
