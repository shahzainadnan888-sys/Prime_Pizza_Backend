"""Reject oversized HTTP request bodies before they are buffered."""

from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.constants import APIMessages, AppConstants
from app.config.settings import Settings


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforce ``MAX_REQUEST_BODY_BYTES`` using Content-Length when present.

    Streaming over-limit without Content-Length is still capped in upload helpers.
    """

    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self._max_bytes = settings.max_request_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            raw = request.headers.get("content-length")
            if raw is not None:
                try:
                    length = int(raw)
                except ValueError:
                    return self._reject(request, message="Invalid Content-Length header")
                if length < 0:
                    return self._reject(request, message="Invalid Content-Length header")
                if length > self._max_bytes:
                    return self._reject(
                        request,
                        message=APIMessages.PAYLOAD_TOO_LARGE,
                        status_code=413,
                        details={"max_bytes": self._max_bytes},
                    )
        return await call_next(request)

    def _reject(
        self,
        request: Request,
        *,
        message: str,
        status_code: int = 400,
        details: dict[str, object] | None = None,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        headers: dict[str, str] = {}
        if request_id:
            headers[AppConstants.REQUEST_ID_HEADER] = str(request_id)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "error": {
                    "code": "payload_too_large" if status_code == 413 else "invalid_content_length",
                    "details": details,
                },
                "request_id": request_id,
                "status_code": status_code,
            },
            headers=headers,
        )
