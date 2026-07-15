"""Application-wide constants."""

from __future__ import annotations


class AppConstants:
    """Immutable application constants."""

    PROJECT_NAME: str = "Prime Pizza"
    API_TITLE: str = "Prime Pizza API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = (
        "Production backend for the Prime Pizza restaurant platform. "
        "Email/password authentication, catalog, cart, checkout, orders, and kitchen operations. "
        "Authenticate with `Authorization: Bearer <access_token>` obtained from `/api/v1/auth/login`. "
        "Errors use a consistent JSON envelope; never expose stack traces to clients."
    )
    DEFAULT_PAGE: int = 1
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    REQUEST_ID_HEADER: str = "X-Request-ID"
    PROCESS_TIME_HEADER: str = "X-Process-Time"


class APIMessages:
    """Standard API user-facing messages."""

    SUCCESS: str = "Success"
    CREATED: str = "Resource created successfully"
    UPDATED: str = "Resource updated successfully"
    DELETED: str = "Resource deleted successfully"
    NOT_FOUND: str = "Resource not found"
    VALIDATION_ERROR: str = "Validation error"
    INTERNAL_ERROR: str = "An unexpected error occurred"
    SERVICE_UNAVAILABLE: str = "Service temporarily unavailable"
    UNAUTHORIZED: str = "Authentication required"
    FORBIDDEN: str = "Insufficient permissions"
    HEALTHY: str = "Service is healthy"
    UNHEALTHY: str = "Service is unhealthy"
    RATE_LIMITED: str = "Too many requests. Please try again later."
    DEGRADED: str = "Service is degraded"
    PAYLOAD_TOO_LARGE: str = "Request body exceeds the maximum allowed size"
    MAINTENANCE: str = "The service is temporarily unavailable for maintenance"
