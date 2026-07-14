"""Owner dashboard statistics, analytics, and chart data."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import OrderStatus
from app.repositories.dashboard import DashboardRepository
from app.schemas.admin_dashboard import (
    AnalyticsPeriod,
    AnalyticsSummaryResponse,
    ChartPoint,
    ChartSeriesResponse,
    ChartsBundleResponse,
    DashboardStatsResponse,
    NamedCount,
)
from app.services.base import BaseService
from app.services.dashboard_cache import DashboardCacheService
from app.services.pricing import money


class DashboardService(BaseService):
    service_name = "dashboard"

    def __init__(
        self,
        *,
        session: AsyncSession,
        cache: DashboardCacheService,
    ) -> None:
        self._session = session
        self._repo = DashboardRepository(session)
        self._cache = cache

    def _period_window(self, period: AnalyticsPeriod, now: datetime) -> tuple[datetime, datetime, str]:
        if period == "daily":
            start = datetime(now.year, now.month, now.day, tzinfo=UTC)
            return start, start + timedelta(days=1), "hour"
        if period == "weekly":
            start = datetime(now.year, now.month, now.day, tzinfo=UTC) - timedelta(days=now.weekday())
            return start, start + timedelta(days=7), "day"
        if period == "monthly":
            start = datetime(now.year, now.month, 1, tzinfo=UTC)
            if now.month == 12:
                end = datetime(now.year + 1, 1, 1, tzinfo=UTC)
            else:
                end = datetime(now.year, now.month + 1, 1, tzinfo=UTC)
            return start, end, "day"
        start = datetime(now.year, 1, 1, tzinfo=UTC)
        return start, datetime(now.year + 1, 1, 1, tzinfo=UTC), "month"

    async def get_stats(self) -> DashboardStatsResponse:
        cached = await self._cache.get_json(self._cache.stats_key())
        if cached is not None:
            return DashboardStatsResponse.model_validate(cached)

        now = datetime.now(UTC)
        today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        tomorrow = today_start + timedelta(days=1)
        month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        year_start = datetime(now.year, 1, 1, tzinfo=UTC)

        today_revenue = await self._repo.revenue_between(today_start, tomorrow)
        today_orders = await self._repo.order_count_between(today_start, tomorrow)
        today_customers = await self._repo.customer_count_between(today_start, tomorrow)
        aov = money(today_revenue / today_orders) if today_orders else money(0)
        status_counts = await self._repo.order_status_counts()
        (
            total_customers,
            total_products,
            total_categories,
            total_deals,
            total_coupons,
        ) = await self._repo.catalog_totals()
        monthly_revenue = await self._repo.revenue_between(month_start, tomorrow)
        yearly_revenue = await self._repo.revenue_between(year_start, tomorrow)

        stats = DashboardStatsResponse(
            today_revenue=today_revenue,
            today_orders=today_orders,
            today_customers=today_customers,
            today_average_order_value=aov,
            pending_orders=status_counts[OrderStatus.PENDING],
            preparing_orders=status_counts[OrderStatus.PREPARING],
            ready_orders=status_counts[OrderStatus.READY],
            out_for_delivery_orders=status_counts[OrderStatus.OUT_FOR_DELIVERY],
            delivered_orders=status_counts[OrderStatus.DELIVERED],
            cancelled_orders=status_counts[OrderStatus.CANCELLED],
            total_customers=total_customers,
            total_products=total_products,
            total_categories=total_categories,
            total_deals=total_deals,
            total_coupons=total_coupons,
            monthly_revenue=monthly_revenue,
            yearly_revenue=yearly_revenue,
            generated_at=now,
        )
        await self._cache.set_json(self._cache.stats_key(), stats.model_dump(mode="json"))
        logger.info("Analytics generated | surface=dashboard_stats")
        return stats

    async def get_analytics(
        self,
        *,
        period: AnalyticsPeriod = "daily",
        limit: int = 10,
    ) -> AnalyticsSummaryResponse:
        cache_key = self._cache.analytics_key(period, f"lim{limit}")
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return AnalyticsSummaryResponse.model_validate(cached)

        now = datetime.now(UTC)
        start, end, _trunc = self._period_window(period, now)
        prev_delta = end - start
        prev_start, prev_end = start - prev_delta, start

        revenue = await self._repo.revenue_between(start, end)
        orders = await self._repo.order_count_between(start, end)
        customers = await self._repo.customer_count_between(start, end)
        cancelled = await self._repo.cancelled_between(start, end)
        prev_customers = await self._repo.customer_count_between(prev_start, prev_end)
        aov = money(revenue / orders) if orders else money(0)
        cancel_rate = money(Decimal(cancelled) * 100 / Decimal(orders)) if orders else money(0)

        tops = await self._repo.top_products(start=start, end=end, limit=limit)
        summary = AnalyticsSummaryResponse(
            period=period,
            revenue=revenue,
            orders=orders,
            customers=customers,
            average_order_value=aov,
            cancellation_rate=cancel_rate,
            customer_growth=customers - prev_customers,
            popular_products=[
                NamedCount(id=item.id, name=item.name, count=item.count) for item in tops
            ],
            popular_categories=await self._repo.top_categories(start=start, end=end, limit=limit),
            best_selling_products=tops,
            most_ordered_deals=await self._repo.top_deals(limit=limit),
            generated_at=now,
        )
        await self._cache.set_json(cache_key, summary.model_dump(mode="json"))
        logger.info("Analytics generated | period={}", period)
        return summary

    def _to_series(
        self,
        *,
        metric: str,
        period: AnalyticsPeriod,
        rows: list[tuple[datetime, Decimal | int]],
        now: datetime,
    ) -> ChartSeriesResponse:
        return ChartSeriesResponse(
            metric=metric,
            period=period,
            points=[
                ChartPoint(label=bucket.isoformat(), value=value)
                for bucket, value in rows
            ],
            generated_at=now,
        )

    async def get_charts(self, *, period: AnalyticsPeriod = "daily") -> ChartsBundleResponse:
        cache_key = self._cache.charts_key(period)
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return ChartsBundleResponse.model_validate(cached)

        now = datetime.now(UTC)
        start, end, trunc = self._period_window(period, now)
        revenue_rows = await self._repo.series_revenue(start=start, end=end, trunc=trunc)
        order_rows = await self._repo.series_orders(start=start, end=end, trunc=trunc)
        customer_rows = await self._repo.series_customers(start=start, end=end, trunc=trunc)
        top_products = await self._repo.top_products(start=start, end=end, limit=10)
        top_categories = await self._repo.top_categories(start=start, end=end, limit=10)
        top_deals = await self._repo.top_deals(limit=10)

        revenue_chart = self._to_series(metric="revenue", period=period, rows=revenue_rows, now=now)
        bundle = ChartsBundleResponse(
            revenue_chart=revenue_chart,
            orders_chart=self._to_series(metric="orders", period=period, rows=order_rows, now=now),
            customers_chart=self._to_series(
                metric="customers", period=period, rows=customer_rows, now=now
            ),
            sales_trend=revenue_chart,
            category_distribution=top_categories,
            top_products=top_products,
            top_deals=top_deals,
            generated_at=now,
        )
        await self._cache.set_json(cache_key, bundle.model_dump(mode="json"))
        return bundle
