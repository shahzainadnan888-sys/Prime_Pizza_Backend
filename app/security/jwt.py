"""JWT access / refresh token service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt

from app.config.settings import Settings
from app.core.exceptions import ExpiredTokenException, InvalidTokenException
from app.security.helpers import generate_secure_token


class JWTService:
    """Create and validate signed JWT access and refresh tokens."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def access_token_expires_seconds(self) -> int:
        return self._settings.access_token_expire_minutes * 60

    def _encode(self, payload: dict[str, Any]) -> str:
        return jwt.encode(
            payload,
            self._settings.secret_key,
            algorithm="HS256",
        )

    def create_token_pair(
        self,
        *,
        user_id: UUID,
        phone_number: str,
        role: str,
    ) -> tuple[str, str, str, str]:
        """
        Return (access_token, refresh_token, access_jti, refresh_jti).
        """
        now = datetime.now(UTC)
        access_jti = generate_secure_token(16)
        refresh_jti = generate_secure_token(16)
        user_id_str = str(user_id)

        access_payload = {
            "sub": user_id_str,
            "user_id": user_id_str,
            "phone_number": phone_number,
            "role": role,
            "token_type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.access_token_expire_minutes),
            "jti": access_jti,
        }
        refresh_payload = {
            "sub": user_id_str,
            "user_id": user_id_str,
            "phone_number": phone_number,
            "role": role,
            "token_type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self._settings.refresh_token_expire_days),
            "jti": refresh_jti,
        }
        return (
            self._encode(access_payload),
            self._encode(refresh_payload),
            access_jti,
            refresh_jti,
        )

    def decode_token(self, token: str, *, expected_type: str | None = None) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=["HS256"],
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenException("Token has expired") from exc
        except JWTError as exc:
            raise InvalidTokenException("Invalid token") from exc

        if expected_type is not None and payload.get("token_type") != expected_type:
            raise InvalidTokenException(f"Expected a {expected_type} token")

        return payload

    def get_remaining_ttl_seconds(self, payload: dict[str, Any]) -> int:
        exp = payload.get("exp")
        if exp is None:
            return 0
        exp_ts = exp.timestamp() if isinstance(exp, datetime) else float(exp)
        remaining = int(exp_ts - datetime.now(UTC).timestamp())
        return max(remaining, 0)
