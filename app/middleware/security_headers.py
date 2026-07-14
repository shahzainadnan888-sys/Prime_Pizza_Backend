"""Security headers middleware."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import Settings

# Swagger UI / ReDoc load assets from CDN + need inline scripts/styles.
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com fonts.googleapis.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
    "font-src 'self' data: fonts.gstatic.com https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

_DOCS_PATH_PREFIXES = ("/docs", "/redoc")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline and production-prep security headers to every response."""

    def __init__(self, app, settings: Settings | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._settings = settings

    @staticmethod
    def _is_docs_path(path: str) -> bool:
        return any(path == prefix or path.startswith(f"{prefix}/") for prefix in _DOCS_PATH_PREFIXES)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # Docs HTML must load CDN scripts; CORP same-site can break some CDN edge cases
        # when combined with strict CSP. Keep same-site for API; cross-origin for docs page shell.
        if self._is_docs_path(request.url.path):
            response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        else:
            response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        settings = self._settings or getattr(request.app.state, "settings", None)
        if settings is not None:
            if settings.enable_csp:
                if self._is_docs_path(request.url.path):
                    # Override any prior CSP so Swagger/ReDoc can render.
                    response.headers["Content-Security-Policy"] = _DOCS_CSP
                else:
                    response.headers.setdefault(
                        "Content-Security-Policy",
                        settings.content_security_policy,
                    )
            # HSTS only when explicitly enabled (requires TLS termination).
            if settings.enable_hsts or settings.is_production:
                max_age = settings.hsts_max_age_seconds
                response.headers.setdefault(
                    "Strict-Transport-Security",
                    f"max-age={max_age}; includeSubDomains; preload",
                )
        return response
