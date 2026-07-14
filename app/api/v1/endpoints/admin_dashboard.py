"""Owner dashboard, analytics, and chart APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from loguru import logger

from app.authorization.permissions import Permission
from app.common.constants import APIMessages
from app.dependencies.admin import get_dashboard_service
from app.dependencies.authorization import require_permission
from app.models.user import User
from app.schemas.admin_dashboard import (
    AnalyticsPeriod,
    AnalyticsSummaryResponse,
    ChartsBundleResponse,
    DashboardStatsResponse,
)
from app.schemas.response import SuccessResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard", response_model=SuccessResponse[DashboardStatsResponse])
async def get_dashboard(
    request: Request,
    user: User = Depends(require_permission(Permission.DASHBOARD_READ)),
    service: DashboardService = Depends(get_dashboard_service),
) -> SuccessResponse[DashboardStatsResponse]:
    logger.info("Dashboard access | user_id={}", user.id)
    data = await service.get_stats()
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/analytics", response_model=SuccessResponse[AnalyticsSummaryResponse])
async def get_analytics(
    request: Request,
    user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    service: DashboardService = Depends(get_dashboard_service),
    period: AnalyticsPeriod = Query(default="daily"),
    limit: int = Query(default=10, ge=1, le=50),
) -> SuccessResponse[AnalyticsSummaryResponse]:
    logger.info("Dashboard access | surface=analytics | user_id={} | period={}", user.id, period)
    data = await service.get_analytics(period=period, limit=limit)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/charts", response_model=SuccessResponse[ChartsBundleResponse])
async def get_charts(
    request: Request,
    user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    service: DashboardService = Depends(get_dashboard_service),
    period: AnalyticsPeriod = Query(default="daily"),
) -> SuccessResponse[ChartsBundleResponse]:
    logger.info("Dashboard access | surface=charts | user_id={} | period={}", user.id, period)
    data = await service.get_charts(period=period)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
