"""Enterprise application exceptions."""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception with HTTP-oriented metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: Any | None = None) -> None:
        super().__init__(
            message,
            code="validation_error",
            status_code=422,
            details=details,
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Any | None = None) -> None:
        super().__init__(
            message,
            code="not_found",
            status_code=404,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Authentication required",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="unauthorized",
            status_code=401,
            details=details,
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="forbidden",
            status_code=403,
            details=details,
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", details: Any | None = None) -> None:
        super().__init__(
            message,
            code="conflict",
            status_code=409,
            details=details,
        )


class DatabaseException(AppException):
    def __init__(
        self,
        message: str = "Database error",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="database_error",
            status_code=503,
            details=details,
        )


class RedisException(AppException):
    def __init__(
        self,
        message: str = "Redis error",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="redis_error",
            status_code=503,
            details=details,
        )


class ExternalServiceException(AppException):
    def __init__(
        self,
        message: str = "External service error",
        *,
        service: str = "unknown",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code=f"{service}_service_error",
            status_code=502,
            details=details,
        )


class RateLimitException(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="rate_limit_exceeded",
            status_code=429,
            details=details,
        )


class InvalidPhoneException(AppException):
    def __init__(
        self,
        message: str = "Invalid phone number",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="invalid_phone",
            status_code=422,
            details=details,
        )


class InvalidOTPException(AppException):
    def __init__(
        self,
        message: str = "Invalid verification code",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="invalid_otp",
            status_code=400,
            details=details,
        )


class ExpiredOTPException(AppException):
    def __init__(
        self,
        message: str = "Verification code has expired",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="expired_otp",
            status_code=400,
            details=details,
        )


class InvalidTokenException(AppException):
    def __init__(
        self,
        message: str = "Invalid token",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="invalid_token",
            status_code=401,
            details=details,
        )


class ExpiredTokenException(AppException):
    def __init__(
        self,
        message: str = "Token has expired",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message,
            code="expired_token",
            status_code=401,
            details=details,
        )
