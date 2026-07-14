"""Pluggable OTP providers (local development now; Twilio/Firebase later)."""

from __future__ import annotations

import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

from loguru import logger

from app.config.settings import Settings
from app.services.base import BaseService


@dataclass(frozen=True)
class GeneratedOTP:
    """Result of creating an OTP challenge."""

    code: str
    expires_in: int
    provider: str


class OTPProvider(ABC):
    """
    Abstract OTP channel.

    Swap ``LocalOTPProvider`` for Twilio/Firebase implementations later without
    changing AuthService orchestration.
    """

    @abstractmethod
    def create_challenge(self, phone_number: str) -> GeneratedOTP:
        """Generate (or dispatch) an OTP for the phone number."""

    @abstractmethod
    def verify_challenge(self, phone_number: str, code: str, expected_code: str) -> bool:
        """
        Verify a submitted code.

        ``expected_code`` is the Redis-stored value for local providers.
        Remote providers may ignore it and call their API instead.
        """


class LocalOTPProvider(OTPProvider, BaseService):
    """Cryptographically secure 6-digit OTP for local / provider-free auth."""

    service_name = "local_otp"
    provider_name = "local"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_challenge(self, phone_number: str) -> GeneratedOTP:
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_in = self._settings.otp_expire_seconds
        self._print_development_banner(phone_number=phone_number, code=code, expires_in=expires_in)
        logger.info(
            "Local OTP generated | phone={} | provider={} | expires_in={}",
            phone_number,
            self.provider_name,
            expires_in,
        )
        return GeneratedOTP(code=code, expires_in=expires_in, provider=self.provider_name)

    def verify_challenge(self, phone_number: str, code: str, expected_code: str) -> bool:
        submitted = (code or "").strip()
        expected = (expected_code or "").strip()
        if not submitted or not expected:
            return False
        # Constant-time compare for equal-length digit codes.
        if len(submitted) != len(expected):
            return False
        return secrets.compare_digest(submitted, expected)

    def _print_development_banner(self, *, phone_number: str, code: str, expires_in: int) -> None:
        minutes = max(expires_in // 60, 1)
        banner = (
            "\n"
            "==================================================\n"
            "Development OTP\n"
            "\n"
            f"Phone: {phone_number}\n"
            "\n"
            f"OTP: {code}\n"
            "\n"
            f"Expires In: {minutes} Minutes\n"
            "==================================================\n"
        )
        # Always print for the local provider so engineers can log in without SMS.
        print(banner, flush=True)
        logger.warning(
            "Development OTP printed to terminal | phone={} | expires_at={}",
            phone_number,
            datetime.now(UTC).isoformat(),
        )


# Backward-compatible alias used by older imports.
OTPService = LocalOTPProvider
