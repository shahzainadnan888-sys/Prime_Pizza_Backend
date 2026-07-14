#!/usr/bin/env python3
"""Validate that required environment variables are present and Settings load."""

from __future__ import annotations

import sys
from pathlib import Path


def _load_dotenv() -> None:
    """Lightweight .env loader so CLI works without exporting vars."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        import os

        os.environ.setdefault(key, value)


def main() -> int:
    _load_dotenv()

    required = [
        "SECRET_KEY",
        "OWNER_PHONE_NUMBER",
        "OWNER_EMAIL",
        "DATABASE_URL",
        "REDIS_URL",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
        "APP_ENV",
        "FRONTEND_URL",
    ]
    from os import getenv

    recommended = [
        "RESEND_API_KEY",
        "RESEND_FROM_EMAIL",
        "ALLOWED_HOSTS",
        "OTP_EXPIRE_SECONDS",
        "OTP_MAX_ATTEMPTS",
    ]

    missing = [key for key in required if not (getenv(key) or "").strip()]
    if missing:
        print("Environment validation FAILED — missing required variables:", file=sys.stderr)
        for key in missing:
            print(f"  - {key}", file=sys.stderr)
        print(
            "\nCopy .env.example to .env and fill in values. "
            "See DEPLOYMENT.md for provider-specific setup.",
            file=sys.stderr,
        )
        return 1

    try:
        from app.config.settings import Settings, get_settings

        get_settings.cache_clear()
        settings = Settings()
    except Exception as exc:  # noqa: BLE001
        print(f"Environment validation FAILED — invalid configuration:\n{exc}", file=sys.stderr)
        return 1

    warnings = [key for key in recommended if not (getenv(key) or "").strip()]

    print("Environment validation PASSED")
    print(f"  APP_ENV={settings.app_env}")
    print(f"  DEBUG={settings.debug}")
    print(f"  API_V1_PREFIX={settings.api_v1_prefix}")
    print(f"  docs_enabled={settings.docs_enabled}")
    print(f"  email_configured={settings.is_email_configured}")
    print(f"  otp_provider=local")
    print(f"  otp_expire_seconds={settings.otp_expire_seconds}")
    print(f"  owner_phone={settings.owner_phone_number}")
    if warnings:
        print("Recommendations (optional / production):")
        for key in warnings:
            print(f"  - {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
