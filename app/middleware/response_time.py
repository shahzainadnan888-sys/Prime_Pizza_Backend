"""Response timing middleware."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.constants import AppConstants


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Measure and expose request processing time."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers[AppConstants.PROCESS_TIME_HEADER] = f"{elapsed_ms:.2f}ms"
        return response
