"""Authentication orchestration service (phone OTP + JWT)."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.roles import RoleAssignmentService
from app.common.enums import OTPVerificationStatus
from app.config.settings import Settings
from app.core.exceptions import (
    ExpiredOTPException,
    ExpiredTokenException,
    InvalidOTPException,
    InvalidTokenException,
    UnauthorizedException,
)
from app.models.user import User
from app.repositories.otp_log import OTPLogRepository
from app.repositories.redis_auth import RedisOTPRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    MeResponse,
    SendOTPResponse,
    TokenPairResponse,
)
from app.security.jwt import JWTService
from app.services.base import BaseService
from app.services.otp_provider import LocalOTPProvider, OTPProvider
from app.services.phone import PhoneValidationService
from app.services.user_sync import UserSyncService


class AuthService(BaseService):
    """Complete phone-OTP authentication use-cases."""

    service_name = "auth"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        redis_auth: RedisOTPRepository,
        otp_provider: OTPProvider,
        jwt_service: JWTService,
        phone_service: PhoneValidationService,
        user_sync: UserSyncService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._redis_auth = redis_auth
        self._otp_provider = otp_provider
        self._jwt = jwt_service
        self._phone = phone_service
        self._user_sync = user_sync
        self._users = UserRepository(session)
        self._otp_logs = OTPLogRepository(session)
        self._role_assignment = RoleAssignmentService(settings)

    async def send_otp(self, phone_number: str, *, client_ip: str | None = None) -> SendOTPResponse:
        phone = self._phone.normalize_and_validate(phone_number)
        await self._redis_auth.enforce_send_rate_limit(phone, client_ip=client_ip)

        challenge = self._otp_provider.create_challenge(phone)
        await self._redis_auth.create_session(
            phone_number=phone,
            otp=challenge.code,
            provider=challenge.provider,
        )
        await self._otp_logs.record_send(
            phone_number=phone,
            provider_sid=challenge.provider,
            expire_seconds=challenge.expires_in,
        )
        await self._session.commit()

        logger.info("OTP requested | phone={} | provider={}", phone, challenge.provider)
        response = SendOTPResponse(
            phone_number=phone,
            expires_in=challenge.expires_in,
            message="Verification code sent",
        )
        # Expose OTP only in development for frontend convenience.
        if self._settings.app_env == "development":
            response.otp = challenge.code
        return response

    async def verify_otp(
        self,
        phone_number: str,
        code: str,
        *,
        client_ip: str | None = None,
    ) -> AuthResponse:
        phone = self._phone.normalize_and_validate(phone_number)
        await self._redis_auth.enforce_verify_rate_limit(phone, client_ip=client_ip)

        try:
            session = await self._redis_auth.get_session(phone)
        except ExpiredOTPException:
            await self._otp_logs.record_result(
                phone_number=phone,
                status=OTPVerificationStatus.EXPIRED,
                attempt_count=0,
                provider_sid=None,
            )
            await self._session.commit()
            raise

        if session.failed_attempts >= self._settings.otp_max_attempts:
            await self._otp_logs.record_result(
                phone_number=phone,
                status=OTPVerificationStatus.FAILED,
                attempt_count=session.failed_attempts,
                provider_sid=session.provider_sid or session.provider,
            )
            await self._session.commit()
            await self._redis_auth.delete_session(phone)
            raise InvalidOTPException("Too many invalid verification attempts")

        approved = self._otp_provider.verify_challenge(phone, code, session.otp)
        if not approved:
            session.failed_attempts += 1
            await self._redis_auth.save_session(session)
            await self._otp_logs.record_result(
                phone_number=phone,
                status=OTPVerificationStatus.FAILED,
                attempt_count=session.failed_attempts,
                provider_sid=session.provider_sid or session.provider,
            )
            await self._session.commit()
            logger.info(
                "Login failed | reason=invalid_otp | phone={} | attempts={}",
                phone,
                session.failed_attempts,
            )
            if session.failed_attempts >= self._settings.otp_max_attempts:
                await self._redis_auth.delete_session(phone)
                raise InvalidOTPException("Too many invalid verification attempts")
            raise InvalidOTPException("Invalid verification code")

        user, is_new = await self._get_or_create_user(phone)
        await self._otp_logs.record_result(
            phone_number=phone,
            status=OTPVerificationStatus.VERIFIED,
            attempt_count=session.failed_attempts,
            provider_sid=session.provider_sid or session.provider,
        )
        await self._session.commit()

        # Delete OTP immediately after successful verification.
        await self._redis_auth.delete_session(phone)
        await self._user_sync.sync_user_best_effort(user)

        tokens = await self._issue_tokens(user)
        logger.info(
            "Login success | phone={} | user_id={} | role={} | is_new_user={}",
            phone,
            user.id,
            user.role,
            is_new,
        )
        return AuthResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
            is_new_user=is_new,
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

    async def _get_or_create_user(self, phone: str) -> tuple[User, bool]:
        role = self._role_assignment.resolve_role(phone)
        existing = await self._users.get_by_phone(phone)
        if existing is not None:
            previous_role = existing.role
            await self._users.mark_login(existing, role=role)
            if previous_role != role:
                logger.info(
                    "Role synchronized from owner phone mapping | user_id={} | from={} | to={}",
                    existing.id,
                    previous_role,
                    role,
                )
            return existing, False
        created = await self._users.create_user(phone_number=phone, role=role)
        logger.info(
            "User created with role | user_id={} | role={} | phone={}",
            created.id,
            role,
            phone,
        )
        return created, True

    async def _issue_tokens(self, user: User) -> TokenPairResponse:
        access, refresh, _access_jti, refresh_jti = self._jwt.create_token_pair(
            user_id=user.id,
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


def build_default_otp_provider(settings: Settings) -> OTPProvider:
    """Factory for the active OTP channel (local until a remote provider is wired)."""
    return LocalOTPProvider(settings)
