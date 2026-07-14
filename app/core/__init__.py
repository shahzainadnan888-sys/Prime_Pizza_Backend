"""Core application cross-cutting concerns."""

from app.core.exceptions import (
    AppException,
    DatabaseException,
    ExpiredOTPException,
    ExpiredTokenException,
    ExternalServiceException,
    InvalidOTPException,
    InvalidPhoneException,
    InvalidTokenException,
    NotFoundException,
    RateLimitException,
    RedisException,
    UnauthorizedException,
    ValidationException,
)
from app.core.logging import setup_logging

__all__ = [
    "AppException",
    "DatabaseException",
    "ExpiredOTPException",
    "ExpiredTokenException",
    "ExternalServiceException",
    "InvalidOTPException",
    "InvalidPhoneException",
    "InvalidTokenException",
    "NotFoundException",
    "RateLimitException",
    "RedisException",
    "UnauthorizedException",
    "ValidationException",
    "setup_logging",
]
