"""Unit tests for local OTP provider."""

from __future__ import annotations

from app.config.settings import get_settings
from app.services.otp_provider import LocalOTPProvider


def test_local_otp_generates_six_digits() -> None:
    provider = LocalOTPProvider(get_settings())
    challenge = provider.create_challenge("+923348957141")
    assert len(challenge.code) == 6
    assert challenge.code.isdigit()
    assert challenge.expires_in >= 60
    assert challenge.provider == "local"


def test_local_otp_verify_constant_time() -> None:
    provider = LocalOTPProvider(get_settings())
    assert provider.verify_challenge("+1", "123456", "123456") is True
    assert provider.verify_challenge("+1", "000000", "123456") is False
    assert provider.verify_challenge("+1", "12345", "123456") is False
