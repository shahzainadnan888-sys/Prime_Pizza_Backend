"""Authentication FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.permissions import permissions_for_role
from app.authorization.policy import AuthorizationService
from app.config.settings import Settings
from app.core.exceptions import InvalidTokenException, UnauthorizedException
from app.dependencies.database import get_db_session
from app.dependencies.redis import get_redis_client
from app.dependencies.settings import get_app_settings
from app.models.user import User
from app.repositories.redis_auth import RedisAuthRepository
from app.repositories.user import UserRepository
from app.security.jwt import JWTService
from app.dependencies.email import get_email_service
from app.services.auth import AuthService
from app.services.email_service import EmailService
from app.services.user_sync import UserSyncService

_bearer = HTTPBearer(auto_error=False)


def get_jwt_service(settings: Settings = Depends(get_app_settings)) -> JWTService:
    return JWTService(settings)


def get_user_sync_service() -> UserSyncService:
    return UserSyncService()


def get_redis_auth_repository(
    redis: Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_app_settings),
) -> RedisAuthRepository:
    return RedisAuthRepository(redis, settings)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    redis_auth: RedisAuthRepository = Depends(get_redis_auth_repository),
    jwt_service: JWTService = Depends(get_jwt_service),
    user_sync: UserSyncService = Depends(get_user_sync_service),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(
        session=session,
        settings=settings,
        redis_auth=redis_auth,
        jwt_service=jwt_service,
        user_sync=user_sync,
        email_service=email_service,
    )


async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    jwt_service: JWTService = Depends(get_jwt_service),
    redis_auth: RedisAuthRepository = Depends(get_redis_auth_repository),
) -> dict:
    """Validate Bearer access token and return claims."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Authentication required")

    payload = jwt_service.decode_token(credentials.credentials, expected_type="access")
    jti = str(payload.get("jti") or "")
    if jti and await redis_auth.is_blacklisted(jti):
        raise InvalidTokenException("Token has been revoked")
    return payload


async def get_current_user(
    request: Request,
    payload: dict = Depends(get_token_payload),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Resolve the authenticated user from a valid access token.

    Authorization always uses the database role — JWT `role` claims are not trusted
    for privilege decisions (prevents privilege escalation via forged/stale claims).
    """
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise InvalidTokenException("Token missing subject")

    repo = UserRepository(session)
    user = await repo.get_by_id(UUID(str(user_id)))
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    jwt_role = str(payload.get("role") or "")
    db_role = str(user.role.value if hasattr(user.role, "value") else user.role)
    if jwt_role and jwt_role != db_role:
        logger.warning(
            "JWT role mismatch ignored | user_id={} | jwt_role={} | db_role={}",
            user.id,
            jwt_role,
            db_role,
        )

    request.state.user = user
    request.state.token_payload = payload
    request.state.authorization_role = db_role
    request.state.permissions = [str(p) for p in permissions_for_role(user.role)]
    return user


async def get_authenticated_user(user: User = Depends(get_current_user)) -> User:
    """Alias dependency for authenticated principals."""
    return user


async def get_verified_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the authenticated user has a verified account."""
    if not user.is_verified:
        raise UnauthorizedException("Account verification required")
    return user


async def get_current_chef(user: User = Depends(get_verified_user)) -> User:
    """Require an active, verified kitchen chef — customers receive HTTP 403."""
    return AuthorizationService().require_chef(user)


# Backward-compatible alias used by older imports
get_current_owner = get_current_chef
