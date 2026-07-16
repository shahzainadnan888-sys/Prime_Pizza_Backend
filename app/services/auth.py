"""Authentication orchestration service (email/password + JWT)."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.roles import RoleAssignmentService
from app.common.enums import UserRole
from app.config.settings import Settings
from app.core.exceptions import (
    ConflictException,
    ExpiredTokenException,
    InvalidTokenException,
    UnauthorizedException,
    ValidationException,
)
from app.models.user import User
from app.repositories.redis_auth import RedisAuthRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenPairResponse,
)
from app.security.jwt import JWTService
from app.security.passwords import hash_password, verify_password
from app.services.base import BaseService
from app.services.email_service import EmailService
from app.services.user_sync import UserSyncService


class AuthService(BaseService):
    """Email/password registration, login, and token lifecycle."""

    service_name = "auth"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        redis_auth: RedisAuthRepository,
        jwt_service: JWTService,
        user_sync: UserSyncService,
        email_service: EmailService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._redis_auth = redis_auth
        self._jwt = jwt_service
        self._user_sync = user_sync
        self._email = email_service
        self._users = UserRepository(session)

    async def register(
        self,
        payload: RegisterRequest,
        *,
        client_ip: str | None = None,
    ) -> AuthResponse:
        email = payload.email.strip().lower()
        await self._redis_auth.enforce_register_rate_limit(email, client_ip=client_ip)

        if await self._users.get_by_email(email) is not None:
            raise ConflictException("An account with this email already exists")

        if payload.phone_number and await self._users.get_by_phone(payload.phone_number) is not None:
            raise ConflictException("An account with this phone number already exists")

        user = await self._users.create_registered_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=email,
            password_hash=hash_password(payload.password),
            phone_number=payload.phone_number,
            role=UserRole.CUSTOMER,
        )
        await self._session.commit()
        await self._session.refresh(user)

        # Send welcome immediately after commit (before mirror sync / token work).
        if self._email is not None:
            try:
                await self._email.notify_welcome_registration(
                    customer_name=user.full_name or user.first_name,
                    customer_email=email,
                )
            except Exception:
                logger.exception(
                    "Welcome email failed after registration | user_id={} | email={}",
                    user.id,
                    email,
                )

        await self._user_sync.sync_user_best_effort(user)

        tokens = await self._issue_tokens(user)
        logger.info(
            "Registration success | user_id={} | email={} | role={}",
            user.id,
            email,
            user.role,
        )
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
            is_new_user=True,
        )

    async def login(
        self,
        payload: LoginRequest,
        *,
        client_ip: str | None = None,
    ) -> AuthResponse:
        email = payload.email.strip().lower()
        await self._redis_auth.enforce_login_rate_limit(email, client_ip=client_ip)

        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            logger.info("Login failed | reason=unknown_user | email={}", email)
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(payload.password, user.password_hash):
            logger.info("Login failed | reason=bad_password | email={}", email)
            raise UnauthorizedException("Invalid email or password")

        # Keep bootstrap chef credentials authoritative for role.
        user = await self._sync_chef_role_if_needed(user, email)

        await self._users.mark_login(user)
        await self._session.commit()
        await self._session.refresh(user)
        await self._user_sync.sync_user_best_effort(user)

        tokens = await self._issue_tokens(user)
        logger.info("Login success | user_id={} | email={} | role={}", user.id, email, user.role)
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
            is_new_user=False,
        )

    async def refresh(self, refresh_token: str) -> AuthResponse:
        payload = self._jwt.decode_token(refresh_token, expected_type="refresh")
        jti = str(payload.get("jti") or "")
        if not jti:
            raise InvalidTokenException("Refresh token missing jti")

        if await self._redis_auth.is_blacklisted(jti):
            logger.warning("Security event | type=refresh_reuse_blocked | jti={}", jti[:8])
            raise InvalidTokenException("Refresh token has been revoked")

        stored_user_id = await self._redis_auth.consume_refresh_token(jti)
        if stored_user_id is None:
            logger.warning("Security event | type=refresh_unknown | jti={}", jti[:8])
            raise InvalidTokenException("Refresh token is not recognized")

        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id or str(user_id) != str(stored_user_id):
            raise InvalidTokenException("Refresh token subject mismatch")

        user = await self._users.get_by_id(UUID(str(user_id)))
        if user is None or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        user = await self._sync_chef_role_if_needed(user, user.email or "")
        if user.email and RoleAssignmentService(self._settings).is_chef_email(user.email):
            await self._session.commit()
            await self._session.refresh(user)

        await self._redis_auth.blacklist_token(
            jti=jti,
            ttl_seconds=self._jwt.get_remaining_ttl_seconds(payload) or 1,
        )

        tokens = await self._issue_tokens(user)
        logger.info("Refresh success | user_id={}", user.id)
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
            is_new_user=False,
        )

    async def logout(
        self,
        *,
        access_payload: dict | None,
        refresh_token: str | None,
    ) -> None:
        if access_payload:
            jti = str(access_payload.get("jti") or "")
            if jti:
                ttl = self._jwt.get_remaining_ttl_seconds(access_payload)
                if ttl > 0:
                    await self._redis_auth.blacklist_token(jti=jti, ttl_seconds=ttl)

        if refresh_token:
            try:
                refresh_payload = self._jwt.decode_token(refresh_token, expected_type="refresh")
                refresh_jti = str(refresh_payload.get("jti") or "")
                if refresh_jti:
                    await self._redis_auth.revoke_refresh_token(refresh_jti)
                    ttl = self._jwt.get_remaining_ttl_seconds(refresh_payload)
                    if ttl > 0:
                        await self._redis_auth.blacklist_token(jti=refresh_jti, ttl_seconds=ttl)
            except (InvalidTokenException, ExpiredTokenException):
                logger.info("Logout with invalid/expired refresh token (ignored)")
            except Exception:
                logger.info("Logout refresh revoke skipped due to token error")

        user_id = (access_payload or {}).get("user_id") or (access_payload or {}).get("sub")
        logger.info("Logout success | user_id={}", user_id)

    async def get_me(self, user: User) -> MeResponse:
        return MeResponse.model_validate(user)

    async def ensure_chef_account(self) -> User:
        """Idempotently create or refresh the bootstrap kitchen chef account."""
        email = self._settings.chef_email.strip().lower()
        existing = await self._users.get_by_email(email)
        if existing is not None:
            changed = False
            if existing.role != UserRole.CHEF:
                existing.role = UserRole.CHEF
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True
            if not existing.is_verified:
                existing.is_verified = True
                changed = True
            if not verify_password(self._settings.chef_password, existing.password_hash):
                existing.password_hash = hash_password(self._settings.chef_password)
                changed = True
            if changed:
                await self._session.commit()
                await self._session.refresh(existing)
                await self._user_sync.sync_user_best_effort(existing)
                logger.info("Chef account synchronized | user_id={} | email={}", existing.id, email)
            return existing

        chef = await self._users.create_registered_user(
            first_name="Kitchen",
            last_name="Chef",
            email=email,
            password_hash=hash_password(self._settings.chef_password),
            phone_number=None,
            role=UserRole.CHEF,
        )
        await self._session.commit()
        await self._session.refresh(chef)
        await self._user_sync.sync_user_best_effort(chef)
        logger.info("Chef account created | user_id={} | email={}", chef.id, email)
        return chef

    async def _sync_chef_role_if_needed(self, user: User, email: str) -> User:
        """Force bootstrap chef email onto the chef role before token issuance."""
        if not RoleAssignmentService(self._settings).is_chef_email(email):
            return user
        changed = False
        if user.role != UserRole.CHEF:
            logger.warning(
                "Chef email had non-chef role; correcting | user_id={} | role={}",
                user.id,
                user.role,
            )
            user.role = UserRole.CHEF
            changed = True
        if not user.is_verified:
            user.is_verified = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            await self._session.flush()
        return user

    async def _issue_tokens(self, user: User) -> TokenPairResponse:
        if not user.email:
            raise ValidationException("User email is required for token issuance")
        access, refresh, _access_jti, refresh_jti = self._jwt.create_token_pair(
            user_id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            role=str(user.role.value if hasattr(user.role, "value") else user.role),
        )
        refresh_ttl = self._settings.refresh_token_expire_days * 24 * 60 * 60
        await self._redis_auth.store_refresh_token(
            jti=refresh_jti,
            user_id=str(user.id),
            ttl_seconds=refresh_ttl,
        )
        return TokenPairResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=self._jwt.access_token_expires_seconds,
        )
