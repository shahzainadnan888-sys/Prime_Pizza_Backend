"""Redis-backed enterprise HTTP rate limiting middleware."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.constants import APIMessages, AppConstants
from app.config.settings import Settings
from app.integrations.redis.client import get_redis
from app.utils.network import get_client_ip


@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    per_minute: int
    per_hour: int
    burst: int


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Apply per-route-group Redis rate limits (minute / hour / burst).

    Bypass is IP-allowlist only and requires both ``RATE_LIMIT_OWNER_BYPASS``
    and a non-empty ``RATE_LIMIT_BYPASS_IPS``. Auth/upload/email/orders policies
    fail closed when Redis is unavailable; others fail open for availability.
    """

    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    def _policy_for_path(self, path: str, method: str) -> RateLimitPolicy:
        s = self._settings
        lower = path.lower()

        if lower.startswith("/health") or lower in {"/", "/api/v1", "/api/v1/"}:
            return RateLimitPolicy(
                "health",
                s.rate_limit_health_per_minute,
                s.rate_limit_health_per_hour,
                s.rate_limit_health_burst,
            )
        if "/auth/" in lower:
            return RateLimitPolicy(
                "auth",
                s.rate_limit_auth_per_minute,
                s.rate_limit_auth_per_hour,
                s.rate_limit_auth_burst,
            )
        if "/admin/" in lower:
            if "test-email" in lower or "/email" in lower:
                return RateLimitPolicy(
                    "email",
                    s.rate_limit_email_per_minute,
                    s.rate_limit_email_per_hour,
                    s.rate_limit_email_burst,
                )
            if "upload" in lower or (method == "POST" and "images" in lower):
                return RateLimitPolicy(
                    "upload",
                    s.rate_limit_upload_per_minute,
                    s.rate_limit_upload_per_hour,
                    s.rate_limit_upload_burst,
                )
            return RateLimitPolicy(
                "admin",
                s.rate_limit_admin_per_minute,
                s.rate_limit_admin_per_hour,
                s.rate_limit_admin_burst,
            )
        if "/checkout" in lower and method == "POST":
            return RateLimitPolicy(
                "checkout",
                s.rate_limit_checkout_per_minute,
                s.rate_limit_checkout_per_hour,
                s.rate_limit_checkout_burst,
            )
        if "/orders" in lower and method == "POST":
            return RateLimitPolicy(
                "orders",
                s.rate_limit_orders_per_minute,
                s.rate_limit_orders_per_hour,
                s.rate_limit_orders_burst,
            )
        if "/search" in lower:
            return RateLimitPolicy(
                "search",
                s.rate_limit_search_per_minute,
                s.rate_limit_search_per_hour,
                s.rate_limit_search_burst,
            )
        if method in {"POST", "PUT", "PATCH"} and (
            "avatar" in lower or "images" in lower or "upload" in lower
        ):
            return RateLimitPolicy(
                "upload",
                s.rate_limit_upload_per_minute,
                s.rate_limit_upload_per_hour,
                s.rate_limit_upload_burst,
            )
        return RateLimitPolicy(
            "default",
            s.rate_limit_default_per_minute,
            s.rate_limit_default_per_hour,
            s.rate_limit_default_burst,
        )

    async def _increment(self, key: str, window_seconds: int) -> int:
        redis = get_redis()
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        results = await pipe.execute()
        return int(results[0])

    async def _check_windows(
        self,
        *,
        identity: str,
        policy: RateLimitPolicy,
    ) -> tuple[bool, str | None, int]:
        """Return (allowed, retry_after_hint, remaining_burst)."""
        minute_key = f"rl:{policy.name}:{identity}:m:{int(time.time() // 60)}"
        hour_key = f"rl:{policy.name}:{identity}:h:{int(time.time() // 3600)}"
        burst_key = f"rl:{policy.name}:{identity}:b:{int(time.time() // 10)}"

        minute_count = await self._increment(minute_key, 60)
        if minute_count > policy.per_minute:
            return False, "60", max(policy.burst - minute_count, 0)

        hour_count = await self._increment(hour_key, 3600)
        if hour_count > policy.per_hour:
            return False, "3600", max(policy.burst - hour_count, 0)

        burst_count = await self._increment(burst_key, 10)
        if burst_count > policy.burst:
            return False, "10", 0

        remaining = max(policy.burst - burst_count, 0)
        return True, None, remaining

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._settings.rate_limit_enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        policy = self._policy_for_path(path, request.method)
        client_ip = get_client_ip(request, self._settings)

        if (
            self._settings.rate_limit_owner_bypass
            and self._settings.rate_limit_bypass_ips
            and policy.name in {"admin", "email", "upload"}
            and client_ip in self._settings.rate_limit_bypass_ips
        ):
            return await call_next(request)

        try:
            allowed, retry_after, remaining = await self._check_windows(
                identity=client_ip,
                policy=policy,
            )
        except Exception:
            if policy.name in set(self._settings.rate_limit_fail_closed_policies):
                logger.error(
                    "Security event | type=rate_limit_backend_unavailable | policy={} | ip={} | path={}",
                    policy.name,
                    client_ip,
                    path,
                )
                request_id = getattr(request.state, "request_id", None)
                headers = {"Retry-After": "30"}
                if request_id:
                    headers[AppConstants.REQUEST_ID_HEADER] = str(request_id)
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "message": APIMessages.SERVICE_UNAVAILABLE,
                        "error": {"code": "rate_limit_unavailable", "details": {"policy": policy.name}},
                        "request_id": request_id,
                        "status_code": 503,
                    },
                    headers=headers,
                )
            logger.warning("Rate limit check failed open | path={} | ip={}", path, client_ip)
            return await call_next(request)

        if not allowed:
            request_id = getattr(request.state, "request_id", None)
            logger.warning(
                "Security event | type=rate_limit | policy={} | ip={} | path={} | id={}",
                policy.name,
                client_ip,
                path,
                request_id,
            )
            headers = {
                "Retry-After": retry_after or "60",
                "X-RateLimit-Limit": str(policy.per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Policy": policy.name,
            }
            if request_id:
                headers[AppConstants.REQUEST_ID_HEADER] = str(request_id)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": APIMessages.RATE_LIMITED,
                    "error": {
                        "code": "rate_limit_exceeded",
                        "details": {"policy": policy.name},
                    },
                    "request_id": request_id,
                    "status_code": 429,
                },
                headers=headers,
            )

        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(policy.per_minute))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        response.headers.setdefault("X-RateLimit-Policy", policy.name)
        return response
