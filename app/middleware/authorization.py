"""Authorization context middleware — initializes request authz state."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class AuthorizationContextMiddleware(BaseHTTPMiddleware):
    """
    Initialize authorization slots on `request.state`.

    Permissions and role are populated by `get_current_user` after JWT → DB
    resolution (DB role is authoritative — never trust JWT role alone).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.permissions = []
        request.state.authorization_role = None
        return await call_next(request)
