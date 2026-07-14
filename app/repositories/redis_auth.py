"""Redis-backed OTP session and rate-limit storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis

from app.config.settings import Settings
from app.core.exceptions import ExpiredOTPException, RateLimitException, RedisException


@dataclass
class OTPSession:
    """OTP challenge stored under ``otp:{phone_number}``."""

    phone_number: str
    otp: str
    created_at: str
    expires_at: str
    failed_attempts: int
    provider: str = "local"
    provider_sid: str | None = None  # reserved for future remote providers


class RedisOTPRepository:
    """Temporary OTP / rate-limit / JWT state in Redis (never permanent users)."""

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._settings = settings

    def _otp_key(self, phone: str) -> str:
        # Canonical key per product contract.
        return f"otp:{phone}"

    def _legacy_otp_key(self, phone: str) -> str:
        return f"auth:otp:{phone}"

    def _send_rate_key(self, phone: str) -> str:
        return f"auth:rate:send:{phone}"

    def _verify_rate_key(self, phone: str) -> str:
        return f"auth:rate:verify:{phone}"

    def _ip_send_rate_key(self, ip: str) -> str:
        return f"auth:rate:send:ip:{ip}"

    def _ip_verify_rate_key(self, ip: str) -> str:
        return f"auth:rate:verify:ip:{ip}"

    def _global_send_rate_key(self) -> str:
        return "auth:rate:send:global"

    def _blacklist_key(self, jti: str) -> str:
        return f"auth:blacklist:{jti}"

    def _refresh_key(self, jti: str) -> str:
        return f"auth:refresh:{jti}"

    async def enforce_send_rate_limit(self, phone: str, *, client_ip: str | None = None) -> None:
        await self._enforce_limit(
            self._send_rate_key(phone),
            limit=self._settings.otp_send_limit,
            window_seconds=self._settings.otp_send_window_seconds,
            message="Too many OTP requests. Please try again later.",
        )
        if client_ip and client_ip != "unknown":
            await self._enforce_limit(
                self._ip_send_rate_key(client_ip),
                limit=self._settings.otp_ip_send_limit,
                window_seconds=self._settings.otp_ip_send_window_seconds,
                message="Too many OTP requests from this network. Please try again later.",
            )
        await self._enforce_limit(
            self._global_send_rate_key(),
            limit=self._settings.otp_global_send_limit,
            window_seconds=self._settings.otp_global_send_window_seconds,
            message="OTP service is temporarily busy. Please try again later.",
        )

    async def enforce_verify_rate_limit(self, phone: str, *, client_ip: str | None = None) -> None:
        await self._enforce_limit(
            self._verify_rate_key(phone),
            limit=self._settings.otp_verify_limit,
            window_seconds=self._settings.otp_verify_window_seconds,
            message="Too many verification attempts. Please try again later.",
        )
        if client_ip and client_ip != "unknown":
            await self._enforce_limit(
                self._ip_verify_rate_key(client_ip),
                limit=self._settings.otp_ip_verify_limit,
                window_seconds=self._settings.otp_ip_verify_window_seconds,
                message="Too many verification attempts from this network. Please try again later.",
            )

    async def _enforce_limit(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        message: str,
    ) -> None:
        try:
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds, nx=True)
            results = await pipe.execute()
            count = int(results[0])
            if count > limit:
                raise RateLimitException(
                    message,
                    details={"limit": limit, "window_seconds": window_seconds},
                )
        except RateLimitException:
            raise
        except Exception as exc:
            raise RedisException("Rate limit check failed") from exc

    async def create_session(
        self,
        *,
        phone_number: str,
        otp: str,
        provider: str = "local",
        provider_sid: str | None = None,
    ) -> OTPSession:
        now = datetime.now(UTC)
        expires = now.timestamp() + self._settings.otp_expire_seconds
        session = OTPSession(
            phone_number=phone_number,
            otp=otp,
            failed_attempts=0,
            created_at=now.isoformat(),
            expires_at=datetime.fromtimestamp(expires, tz=UTC).isoformat(),
            provider=provider,
            provider_sid=provider_sid,
        )
        try:
            # Clear any legacy key to avoid dual sessions.
            await self._redis.delete(self._legacy_otp_key(phone_number))
            await self._redis.set(
                self._otp_key(phone_number),
                json.dumps(asdict(session)),
                ex=self._settings.otp_expire_seconds,
            )
        except Exception as exc:
            raise RedisException("Failed to store OTP session") from exc
        return session

    def _parse_session(self, data: dict[str, Any]) -> OTPSession:
        # Backward compatible with older Twilio session payloads.
        if "otp" not in data and "provider_sid" in data:
            data = {
                **data,
                "otp": "",
                "failed_attempts": int(data.get("attempt_count") or 0),
                "provider": "legacy",
            }
        if "failed_attempts" not in data and "attempt_count" in data:
            data["failed_attempts"] = int(data.get("attempt_count") or 0)
        return OTPSession(
            phone_number=str(data["phone_number"]),
            otp=str(data.get("otp") or ""),
            created_at=str(data["created_at"]),
            expires_at=str(data["expires_at"]),
            failed_attempts=int(data.get("failed_attempts") or 0),
            provider=str(data.get("provider") or "local"),
            provider_sid=data.get("provider_sid"),
        )

    async def get_session(self, phone_number: str) -> OTPSession:
        try:
            raw = await self._redis.get(self._otp_key(phone_number))
            if not raw:
                raw = await self._redis.get(self._legacy_otp_key(phone_number))
        except Exception as exc:
            raise RedisException("Failed to load OTP session") from exc
        if not raw:
            raise ExpiredOTPException("Verification session not found or expired")
        data: dict[str, Any] = json.loads(raw)
        session = self._parse_session(data)
        expires_at = datetime.fromisoformat(session.expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            await self.delete_session(phone_number)
            raise ExpiredOTPException("Verification code has expired")
        return session

    async def save_session(self, session: OTPSession) -> None:
        try:
            key = self._otp_key(session.phone_number)
            ttl = await self._redis.ttl(key)
            if ttl is None or ttl < 0:
                legacy = self._legacy_otp_key(session.phone_number)
                ttl = await self._redis.ttl(legacy)
                key = legacy if ttl is not None and ttl >= 0 else key
            if ttl is None or ttl < 0:
                raise ExpiredOTPException("Verification session not found or expired")
            await self._redis.set(
                self._otp_key(session.phone_number),
                json.dumps(asdict(session)),
                ex=ttl,
            )
            if key != self._otp_key(session.phone_number):
                await self._redis.delete(key)
        except ExpiredOTPException:
            raise
        except Exception as exc:
            raise RedisException("Failed to update OTP session") from exc

    async def delete_session(self, phone_number: str) -> None:
        try:
            await self._redis.delete(
                self._otp_key(phone_number),
                self._legacy_otp_key(phone_number),
            )
        except Exception as exc:
            raise RedisException("Failed to clear OTP session") from exc

    async def store_refresh_token(self, *, jti: str, user_id: str, ttl_seconds: int) -> None:
        try:
            await self._redis.set(
                self._refresh_key(jti),
                user_id,
                ex=max(ttl_seconds, 1),
            )
        except Exception as exc:
            raise RedisException("Failed to store refresh token") from exc

    async def consume_refresh_token(self, jti: str) -> str | None:
        """Atomically read+delete a refresh token (rotation without reuse races)."""
        try:
            key = self._refresh_key(jti)
            try:
                raw = await self._redis.getdel(key)
            except AttributeError:
                pipe = self._redis.pipeline()
                pipe.get(key)
                pipe.delete(key)
                results = await pipe.execute()
                raw = results[0]
            return str(raw) if raw else None
        except Exception as exc:
            raise RedisException("Failed to consume refresh token") from exc

    async def revoke_refresh_token(self, jti: str) -> None:
        try:
            await self._redis.delete(self._refresh_key(jti))
        except Exception as exc:
            raise RedisException("Failed to revoke refresh token") from exc

    async def blacklist_token(self, *, jti: str, ttl_seconds: int) -> None:
        try:
            await self._redis.set(self._blacklist_key(jti), "1", ex=max(ttl_seconds, 1))
        except Exception as exc:
            raise RedisException("Failed to blacklist token") from exc

    async def is_blacklisted(self, jti: str) -> bool:
        try:
            return bool(await self._redis.exists(self._blacklist_key(jti)))
        except Exception as exc:
            raise RedisException("Failed to check token blacklist") from exc
