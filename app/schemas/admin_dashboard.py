"""Owner dashboard, analytics, and chart schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


AnalyticsPeriod = Literal["daily", "weekly", "monthly", "yearly"]


class NamedCount(BaseModel):
    id: str | None = None
    name: str
    count: int


class NamedMoneyCount(BaseModel):
    id: str | None = None
    name: str
    count: int
    revenue: Decimal


class DashboardStatsResponse(BaseModel):
    today_revenue: Decimal
    today_orders: int
    today_customers: int
    today_average_order_value: Decimal
    pending_orders: int
    preparing_orders: int
    ready_orders: int
    out_for_delivery_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_customers: int
    total_products: int
    total_categories: int
    total_deals: int
    total_coupons: int
    monthly_revenue: Decimal
    yearly_revenue: Decimal
    generated_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    period: AnalyticsPeriod
    revenue: Decimal
    orders: int
    customers: int
    average_order_value: Decimal
    cancellation_rate: Decimal
    customer_growth: int
    popular_products: list[NamedCount]
    popular_categories: list[NamedCount]
    best_selling_products: list[NamedMoneyCount]
    most_ordered_deals: list[NamedCount]
    generated_at: datetime


class ChartPoint(BaseModel):
    label: str
    value: Decimal | int


class ChartSeriesResponse(BaseModel):
    metric: str
    period: AnalyticsPeriod
    points: list[ChartPoint]
    generated_at: datetime


class ChartsBundleResponse(BaseModel):
    revenue_chart: ChartSeriesResponse
    orders_chart: ChartSeriesResponse
    customers_chart: ChartSeriesResponse
    sales_trend: ChartSeriesResponse
    category_distribution: list[NamedCount]
    top_products: list[NamedMoneyCount]
    top_deals: list[NamedCount]
    generated_at: datetime


class AnalyticsQueryParams(BaseModel):
    period: AnalyticsPeriod = "daily"
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=10, ge=1, le=50)
