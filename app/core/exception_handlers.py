"""Global exception handlers returning consistent API error envelopes."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.constants import APIMessages
from app.core.exceptions import AppException, RateLimitException
from app.monitoring.metrics import metrics
from app.schemas.response import ErrorDetail, ErrorResponse

# Codes whose structured details may aid attackers — strip in production.
_SENSITIVE_DETAIL_CODES = {
    "rate_limit_exceeded",
    "forbidden",
    "cloudinary_service_error",
    "brevo_service_error",
    "invalid_phone",
    "database_error",
    "redis_error",
}


def _sanitize_validation_errors(errors: list[Any]) -> list[dict[str, Any]]:
    """Make Pydantic/FastAPI validation errors JSON-serializable."""
    sanitized: list[dict[str, Any]] = []
    for error in errors:
        item = dict(error)
        ctx = item.get("ctx")
        if isinstance(ctx, dict):
            item["ctx"] = {
                key: (str(value) if isinstance(value, BaseException) else value)
                for key, value in ctx.items()
            }
        # Never echo submitted secret-looking values in validation errors
        loc = item.get("loc") or ()
        if any(str(part).lower() in {"password", "otp", "code", "token", "refresh_token"} for part in loc):
            item.pop("input", None)
        sanitized.append(item)
    return sanitized


def _public_details(request: Request, *, code: str, details: Any | None) -> Any | None:
    settings = getattr(request.app.state, "settings", None)
    if settings is None or not settings.is_production:
        return details
    if code in _SENSITIVE_DETAIL_CODES:
        return None
    return details


def _error_payload(
    *,
    code: str,
    message: str,
    status_code: int,
    request: Request,
    details: Any | None = None,
) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", None)
    payload = ErrorResponse(
        success=False,
        message=message,
        error=ErrorDetail(code=code, details=_public_details(request, code=code, details=details)),
        request_id=request_id,
        status_code=status_code,
    )
    return payload.model_dump(mode="json")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach enterprise exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        metrics.incr(f"errors.app.{exc.code}")
        if isinstance(exc, RateLimitException) or exc.status_code in {401, 403}:
            logger.warning(
                "Security event | type=app_exception | code={} | status={} | path={} | message={}",
                exc.code,
                exc.status_code,
                request.url.path,
                exc.message,
            )
        else:
            logger.warning(
                "AppException | code={} | status={} | path={} | message={}",
                exc.code,
                exc.status_code,
                request.url.path,
                exc.message,
            )
        headers: dict[str, str] = {}
        if exc.status_code == 429:
            headers["Retry-After"] = "60"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
                request=request,
                details=exc.details,
            ),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = _sanitize_validation_errors(exc.errors())
        metrics.incr("errors.validation")
        logger.info("Validation error | path={} | errors={}", request.url.path, details)
        unprocessable = getattr(
            status,
            "HTTP_422_UNPROCESSABLE_CONTENT",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        return JSONResponse(
            status_code=unprocessable,
            content=_error_payload(
                code="validation_error",
                message=APIMessages.VALIDATION_ERROR,
                status_code=unprocessable,
                request=request,
                details=details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code="http_error",
                message=detail,
                status_code=exc.status_code,
                request=request,
                details=exc.detail if not isinstance(exc.detail, str) else None,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        metrics.incr("errors.database")
        logger.error("Database error | path={} | error={}", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_payload(
                code="database_error",
                message=APIMessages.SERVICE_UNAVAILABLE,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                request=request,
            ),
        )

    @app.exception_handler(RedisError)
    async def redis_exception_handler(request: Request, exc: RedisError) -> JSONResponse:
        metrics.incr("errors.redis")
        logger.error("Redis error | path={} | error={}", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_payload(
                code="redis_error",
                message=APIMessages.SERVICE_UNAVAILABLE,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                request=request,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        metrics.incr("errors.unhandled")
        logger.exception("Unhandled exception | path={} | error={}", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                code="internal_error",
                message=APIMessages.INTERNAL_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request=request,
            ),
        )
