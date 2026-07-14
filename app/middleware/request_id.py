"""Request ID correlation middleware."""

from __future__ import annotations

import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.constants import AppConstants


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID and bind it into Loguru context."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(AppConstants.REQUEST_ID_HEADER)
        request_id = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())
        # Reject header injection / oversized correlation ids
        if len(request_id) > 128 or any(ch in request_id for ch in ("\r", "\n", "\0")):
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        response.headers[AppConstants.REQUEST_ID_HEADER] = request_id
        return response
