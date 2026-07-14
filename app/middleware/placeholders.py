"""Placeholder middleware retained for compatibility (auth state bootstrap)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class AuthenticationPlaceholderMiddleware(BaseHTTPMiddleware):
    """
    Bootstrap request.state.user.

    Real authentication is resolved via FastAPI dependencies. This middleware
    only initializes the slot so route code can safely getattr without races.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user = None
        return await call_next(request)
