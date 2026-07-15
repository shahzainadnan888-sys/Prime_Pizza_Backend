"""Health and readiness endpoints."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

from app.common.constants import APIMessages, AppConstants
from app.common.enums import HealthStatus
from app.database.session import get_engine
from app.integrations.brevo.client import is_brevo_configured
from app.integrations.cloudinary.client import is_cloudinary_configured
from app.integrations.redis.client import redis_ping
from app.monitoring.metrics import metrics
from app.schemas.health import ComponentHealth, HealthResponse
from app.schemas.response import SuccessResponse

router = APIRouter(tags=["Health"])


def _component(
    *,
    ok: bool,
    latency_ms: float | None = None,
    detail: str | None = None,
) -> dict[str, object]:
    return ComponentHealth(
        status=HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY,
        latency_ms=round(latency_ms, 2) if latency_ms is not None else None,
        detail=detail,
    ).model_dump()


@router.get(
    "/",
    response_model=SuccessResponse[dict[str, str]],
    summary="API root",
)
async def root(request: Request) -> SuccessResponse[dict[str, str]]:
    """Service identity endpoint."""
    settings = request.app.state.settings
    data = {
        "name": settings.app_name,
        "version": AppConstants.API_VERSION,
        "environment": settings.app_env,
    }
    if settings.docs_enabled:
        data["docs"] = "/docs"
        data["redoc"] = "/redoc"
    return SuccessResponse(
        success=True,
        message=f"Welcome to {settings.app_name}",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
)
async def health(request: Request) -> HealthResponse:
    """Process liveness — does not check external dependencies."""
    return HealthResponse(
        success=True,
        message=APIMessages.HEALTHY,
        data={
            "status": HealthStatus.HEALTHY,
            "service": request.app.state.settings.app_name,
            "timestamp": datetime.now(UTC),
        },
    )


@router.get(
    "/health/database",
    response_model=HealthResponse,
    summary="Database readiness",
    responses={503: {"model": HealthResponse}},
)
async def health_database(request: Request) -> JSONResponse:
    """Verify PostgreSQL connectivity."""
    started = time.perf_counter()
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.observe("health.database.latency_ms", latency_ms)
        payload = HealthResponse(
            success=True,
            message="Database is healthy",
            data={"database": _component(ok=True, latency_ms=latency_ms)},
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=payload.model_dump(mode="json"))
    except Exception as exc:
        logger.error("Database health check failed: {}", exc)
        metrics.incr("health.database.failures")
        payload = HealthResponse(
            success=False,
            message="Database is unhealthy",
            data={
                "database": _component(ok=False, detail="Connectivity check failed"),
            },
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload.model_dump(mode="json"),
        )


@router.get(
    "/health/redis",
    response_model=HealthResponse,
    summary="Redis readiness",
    responses={503: {"model": HealthResponse}},
)
async def health_redis(request: Request) -> JSONResponse:
    """Verify Redis connectivity."""
    started = time.perf_counter()
    try:
        ok = await redis_ping()
        latency_ms = (time.perf_counter() - started) * 1000
        if not ok:
            raise RuntimeError("Redis PING returned falsy result")
        metrics.observe("health.redis.latency_ms", latency_ms)
        payload = HealthResponse(
            success=True,
            message="Redis is healthy",
            data={"redis": _component(ok=True, latency_ms=latency_ms)},
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=payload.model_dump(mode="json"))
    except Exception as exc:
        logger.error("Redis health check failed: {}", exc)
        metrics.incr("health.redis.failures")
        payload = HealthResponse(
            success=False,
            message="Redis is unhealthy",
            data={"redis": _component(ok=False, detail="Connectivity check failed")},
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload.model_dump(mode="json"),
        )


@router.get(
    "/health/services",
    response_model=HealthResponse,
    summary="Dependency and configuration readiness",
    responses={503: {"model": HealthResponse}},
)
async def health_services(request: Request) -> JSONResponse:
    """
    Aggregate readiness for database, Redis, and configured third-party services.

    Cloudinary / Brevo checks verify configuration presence (not live
    outbound calls) to avoid costing API credits on every probe.
    """
    settings = request.app.state.settings
    components: dict[str, object] = {}
    overall_ok = True
    degraded = False

    # Database
    started = time.perf_counter()
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        components["database"] = _component(ok=True, latency_ms=(time.perf_counter() - started) * 1000)
    except Exception:
        overall_ok = False
        components["database"] = _component(ok=False, detail="Connectivity check failed")

    # Redis (auth rate limits, refresh tokens, blacklist)
    started = time.perf_counter()
    try:
        ok = await redis_ping()
        if not ok:
            raise RuntimeError("ping failed")
        components["redis"] = _component(ok=True, latency_ms=(time.perf_counter() - started) * 1000)
    except Exception:
        overall_ok = False
        components["redis"] = _component(ok=False, detail="Connectivity check failed")

    # Configuration presence (no live network calls)
    cloudinary_ok = is_cloudinary_configured()
    brevo_ok = is_brevo_configured() or not settings.email_enabled

    components["cloudinary"] = _component(
        ok=cloudinary_ok,
        detail=None if cloudinary_ok else "Cloudinary credentials missing",
    )
    components["brevo"] = _component(
        ok=brevo_ok,
        detail=None if brevo_ok else "Brevo API key missing while EMAIL_ENABLED=true",
    )
    if not cloudinary_ok:
        overall_ok = False
    if not brevo_ok:
        degraded = True

    components["configuration"] = _component(
        ok=True,
        detail=f"env={settings.app_env}; docs={'on' if settings.docs_enabled else 'off'}",
    )
    # Public health must not leak detailed attack-useful metrics. Expose a minimal summary.
    snap = metrics.snapshot()
    components["metrics"] = {
        "uptime_seconds": snap.get("uptime_seconds"),
        "http_requests_total": snap.get("counters", {}).get("http.requests_total", 0),
    }

    if overall_ok and not degraded:
        message = "All services healthy"
        http_status = status.HTTP_200_OK
        success = True
    elif overall_ok and degraded:
        message = APIMessages.DEGRADED
        http_status = status.HTTP_200_OK
        success = True
    else:
        message = "One or more critical services are unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        success = False

    payload = HealthResponse(
        success=success,
        message=message,
        data=components,
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=http_status, content=payload.model_dump(mode="json"))
