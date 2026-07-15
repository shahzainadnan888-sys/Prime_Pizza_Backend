"""Password hashing and strength validation."""

from __future__ import annotations

import re

import bcrypt

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,128}$",
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not hashed_password:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def validate_password_strength(password: str) -> str:
    """
    Enforce a strong password policy for customer registration.

    Requires at least 8 characters with uppercase, lowercase, and a digit.
    """
    value = password.strip()
    if not _PASSWORD_PATTERN.match(value):
        raise ValueError(
            "Password must be 8–128 characters and include uppercase, lowercase, and a digit",
        )
    return value
