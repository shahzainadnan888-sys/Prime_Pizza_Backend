"""FastAPI dependency injection package."""

from app.dependencies.auth import (
    get_auth_service,
    get_authenticated_user,
    get_current_owner,
    get_current_user,
    get_token_payload,
    get_verified_user,
)
from app.dependencies.authorization import (
    ensure_resource_owner,
    get_authorization_service,
    require_any_permission,
    require_authenticated,
    require_customer,
    require_owner,
    require_permission,
    require_self_or_owner,
    require_verified,
)
from app.dependencies.database import get_db_session
from app.dependencies.pagination import get_pagination
from app.dependencies.redis import get_cache_service, get_redis_client
from app.dependencies.settings import get_app_settings

__all__ = [
    "ensure_resource_owner",
    "get_app_settings",
    "get_auth_service",
    "get_authenticated_user",
    "get_authorization_service",
    "get_cache_service",
    "get_current_owner",
    "get_current_user",
    "get_db_session",
    "get_pagination",
    "get_redis_client",
    "get_token_payload",
    "get_verified_user",
    "require_any_permission",
    "require_authenticated",
    "require_customer",
    "require_owner",
    "require_permission",
    "require_self_or_owner",
    "require_verified",
]
