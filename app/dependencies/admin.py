"""FastAPI dependencies for owner dashboard module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.dependencies.database import get_db_session
from app.dependencies.redis import get_cache_service
from app.dependencies.settings import get_app_settings
from app.integrations.redis.cache import CacheService
from app.services.admin_coupon import AdminCouponService
from app.services.admin_customer import AdminCustomerService
from app.services.admin_notification import AdminNotificationService
from app.services.admin_search import AdminSearchService
from app.services.audit import AuditService
from app.services.dashboard import DashboardService
from app.services.dashboard_cache import DashboardCacheService
from app.services.system_settings import SystemSettingsService


def get_dashboard_cache(
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_app_settings),
) -> DashboardCacheService:
    return DashboardCacheService(cache, settings)


def get_audit_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuditService:
    return AuditService(session=session)


def get_dashboard_service(
    session: AsyncSession = Depends(get_db_session),
    cache: DashboardCacheService = Depends(get_dashboard_cache),
) -> DashboardService:
    return DashboardService(session=session, cache=cache)


def get_admin_customer_service(
    session: AsyncSession = Depends(get_db_session),
    audit: AuditService = Depends(get_audit_service),
    dashboard_cache: DashboardCacheService = Depends(get_dashboard_cache),
) -> AdminCustomerService:
    return AdminCustomerService(session=session, audit=audit, dashboard_cache=dashboard_cache)


def get_admin_coupon_service(
    session: AsyncSession = Depends(get_db_session),
    audit: AuditService = Depends(get_audit_service),
    dashboard_cache: DashboardCacheService = Depends(get_dashboard_cache),
) -> AdminCouponService:
    return AdminCouponService(session=session, audit=audit, dashboard_cache=dashboard_cache)


def get_admin_notification_service(
    session: AsyncSession = Depends(get_db_session),
    audit: AuditService = Depends(get_audit_service),
) -> AdminNotificationService:
    return AdminNotificationService(session=session, audit=audit)


def get_system_settings_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    audit: AuditService = Depends(get_audit_service),
    dashboard_cache: DashboardCacheService = Depends(get_dashboard_cache),
    cache: CacheService = Depends(get_cache_service),
) -> SystemSettingsService:
    return SystemSettingsService(
        session=session,
        settings=settings,
        audit=audit,
        dashboard_cache=dashboard_cache,
        cache=cache,
    )


def get_admin_search_service(
    session: AsyncSession = Depends(get_db_session),
) -> AdminSearchService:
    return AdminSearchService(session=session)
