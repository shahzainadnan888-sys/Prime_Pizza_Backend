"""Request/response logging middleware with duration and redaction."""

from __future__ import annotations

import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import metrics
from app.utils.network import get_client_ip


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log inbound requests and outbound status codes without sensitive payloads."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = getattr(request.state, "request_id", "-")
        client_ip = get_client_ip(request)
        started = time.perf_counter()
        logger.info(
            "HTTP request | id={} | method={} | path={} | ip={}",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        metrics.observe("http.request.duration_ms", duration_ms)
        metrics.incr(f"http.status.{response.status_code}")
        metrics.incr("http.requests_total")
        logger.info(
            "HTTP response | id={} | method={} | path={} | status={} | duration_ms={:.2f}",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
