"""Register all HTTP middleware in a deterministic order."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config.settings import Settings
from app.middleware.authorization import AuthorizationContextMiddleware
from app.middleware.maintenance import MaintenanceModeMiddleware
from app.middleware.placeholders import AuthenticationPlaceholderMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size import RequestBodyLimitMiddleware
from app.middleware.response_time import ResponseTimeMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Middleware registration order matters (last added = outermost).

    Effective inbound order:
    TrustedHost → CORS → GZip → SecurityHeaders → RequestID →
    RequestLogging → ResponseTime → BodyLimit → Maintenance →
    Auth placeholder → Authz context → RateLimit → route
    """
    app.add_middleware(RateLimitingMiddleware, settings=settings)
    app.add_middleware(AuthorizationContextMiddleware)
    app.add_middleware(AuthenticationPlaceholderMiddleware)
    app.add_middleware(MaintenanceModeMiddleware, settings=settings)
    app.add_middleware(RequestBodyLimitMiddleware, settings=settings)
    app.add_middleware(ResponseTimeMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Policy",
            "Retry-After",
        ],
    )

    hosts = settings.allowed_hosts
    if settings.is_development and "*" not in hosts:
        hosts = [*hosts, "localhost", "127.0.0.1", "testserver"]

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
