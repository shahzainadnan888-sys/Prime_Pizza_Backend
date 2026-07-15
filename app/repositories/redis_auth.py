"""Redis-backed JWT session state and auth rate limits."""

from __future__ import annotations

from redis.asyncio import Redis

from app.config.settings import Settings
from app.core.exceptions import RateLimitException, RedisException


class RedisAuthRepository:
    """Refresh-token store, JWT blacklist, and login/register rate limits."""

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._settings = settings

    def _login_rate_key(self, identity: str) -> str:
        return f"auth:rate:login:{identity}"

    def _register_rate_key(self, identity: str) -> str:
        return f"auth:rate:register:{identity}"

    def _ip_auth_rate_key(self, ip: str) -> str:
        return f"auth:rate:ip:{ip}"

    def _blacklist_key(self, jti: str) -> str:
        return f"auth:blacklist:{jti}"

    def _refresh_key(self, jti: str) -> str:
        return f"auth:refresh:{jti}"

    async def enforce_login_rate_limit(self, identity: str, *, client_ip: str | None = None) -> None:
        await self._enforce_limit(
            self._login_rate_key(identity),
            limit=self._settings.auth_login_limit,
            window_seconds=self._settings.auth_login_window_seconds,
            message="Too many login attempts. Please try again later.",
        )
        if client_ip and client_ip != "unknown":
            await self._enforce_limit(
                self._ip_auth_rate_key(client_ip),
                limit=self._settings.auth_ip_limit,
                window_seconds=self._settings.auth_ip_window_seconds,
                message="Too many authentication attempts from this network.",
            )

    async def enforce_register_rate_limit(self, identity: str, *, client_ip: str | None = None) -> None:
        await self._enforce_limit(
            self._register_rate_key(identity),
            limit=self._settings.auth_register_limit,
            window_seconds=self._settings.auth_register_window_seconds,
            message="Too many registration attempts. Please try again later.",
        )
        if client_ip and client_ip != "unknown":
            await self._enforce_limit(
                self._ip_auth_rate_key(client_ip),
                limit=self._settings.auth_ip_limit,
                window_seconds=self._settings.auth_ip_window_seconds,
                message="Too many authentication attempts from this network.",
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
