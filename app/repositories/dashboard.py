"""Aggregation queries for owner dashboard and analytics."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import OrderStatus, UserRole
from app.models.catalog import Category, Product
from app.models.coupon import Coupon
from app.models.deal import Deal
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.admin_dashboard import NamedCount, NamedMoneyCount


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _revenue_filter(self) -> object:
        return and_(
            Order.deleted_at.is_(None),
            Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
        )

    async def revenue_between(self, start: datetime, end: datetime) -> Decimal:
        stmt = select(func.coalesce(func.sum(Order.grand_total), 0)).where(
            self._revenue_filter(),
            Order.created_at >= start,
            Order.created_at < end,
        )
        return Decimal(str((await self.session.execute(stmt)).scalar_one()))

    async def order_count_between(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count()).select_from(Order).where(
            Order.deleted_at.is_(None),
            Order.created_at >= start,
            Order.created_at < end,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def customer_count_between(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count()).select_from(User).where(
            User.deleted_at.is_(None),
            User.role == UserRole.CUSTOMER,
            User.created_at >= start,
            User.created_at < end,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_orders_by_status(self, status: OrderStatus) -> int:
        stmt = select(func.count()).select_from(Order).where(
            Order.deleted_at.is_(None),
            Order.status == status,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_customers(self) -> int:
        stmt = select(func.count()).select_from(User).where(
            User.deleted_at.is_(None),
            User.role == UserRole.CUSTOMER,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_products(self) -> int:
        stmt = select(func.count()).select_from(Product).where(Product.deleted_at.is_(None))
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_categories(self) -> int:
        stmt = select(func.count()).select_from(Category).where(Category.deleted_at.is_(None))
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_deals(self) -> int:
        stmt = select(func.count()).select_from(Deal).where(Deal.deleted_at.is_(None))
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_coupons(self) -> int:
        stmt = select(func.count()).select_from(Coupon).where(Coupon.deleted_at.is_(None))
        return int((await self.session.execute(stmt)).scalar_one())

    async def order_status_counts(self) -> dict[OrderStatus, int]:
        """Single query for open-status inventory on the dashboard."""
        stmt = (
            select(Order.status, func.count().label("cnt"))
            .where(Order.deleted_at.is_(None))
            .group_by(Order.status)
        )
        rows = (await self.session.execute(stmt)).all()
        counts = {status: 0 for status in OrderStatus}
        for row in rows:
            counts[row.status] = int(row.cnt)
        return counts

    async def catalog_totals(self) -> tuple[int, int, int, int, int]:
        """Return customers, products, categories, deals, coupons in five light counts."""
        customers = await self.count_customers()
        products = await self.count_products()
        categories = await self.count_categories()
        deals = await self.count_deals()
        coupons = await self.count_coupons()
        return customers, products, categories, deals, coupons

    async def cancelled_between(self, start: datetime, end: datetime) -> int:
        stmt = select(func.count()).select_from(Order).where(
            Order.deleted_at.is_(None),
            Order.status == OrderStatus.CANCELLED,
            Order.created_at >= start,
            Order.created_at < end,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def series_orders(
        self,
        *,
        start: datetime,
        end: datetime,
        trunc: str,
    ) -> list[tuple[datetime, int]]:
        bucket = func.date_trunc(trunc, Order.created_at)
        stmt = (
            select(bucket.label("bucket"), func.count().label("cnt"))
            .where(
                Order.deleted_at.is_(None),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .group_by(text("1"))
            .order_by(text("1"))
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row.bucket, int(row.cnt)) for row in rows]

    async def series_revenue(
        self,
        *,
        start: datetime,
        end: datetime,
        trunc: str,
    ) -> list[tuple[datetime, Decimal]]:
        bucket = func.date_trunc(trunc, Order.created_at)
        stmt = (
            select(
                bucket.label("bucket"),
                func.coalesce(func.sum(Order.grand_total), 0).label("revenue"),
            )
            .where(
                self._revenue_filter(),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .group_by(text("1"))
            .order_by(text("1"))
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row.bucket, Decimal(str(row.revenue))) for row in rows]

    async def series_customers(
        self,
        *,
        start: datetime,
        end: datetime,
        trunc: str,
    ) -> list[tuple[datetime, int]]:
        bucket = func.date_trunc(trunc, User.created_at)
        stmt = (
            select(bucket.label("bucket"), func.count().label("cnt"))
            .where(
                User.deleted_at.is_(None),
                User.role == UserRole.CUSTOMER,
                User.created_at >= start,
                User.created_at < end,
            )
            .group_by(text("1"))
            .order_by(text("1"))
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row.bucket, int(row.cnt)) for row in rows]

    async def top_products(
        self,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[NamedMoneyCount]:
        stmt = (
            select(
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("qty"),
                func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                OrderItem.deleted_at.is_(None),
                Order.deleted_at.is_(None),
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .group_by(OrderItem.product_id, OrderItem.product_name)
            .order_by(text("qty DESC"))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            NamedMoneyCount(
                id=str(row.product_id) if row.product_id else None,
                name=row.product_name,
                count=int(row.qty),
                revenue=Decimal(str(row.revenue)),
            )
            for row in rows
        ]

    async def top_categories(
        self,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[NamedCount]:
        stmt = (
            select(
                Category.id,
                Category.name,
                func.sum(OrderItem.quantity).label("qty"),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .join(Category, Category.id == Product.category_id)
            .where(
                OrderItem.deleted_at.is_(None),
                Order.deleted_at.is_(None),
                Product.deleted_at.is_(None),
                Category.deleted_at.is_(None),
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .group_by(Category.id, Category.name)
            .order_by(text("qty DESC"))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            NamedCount(id=str(row.id), name=row.name, count=int(row.qty)) for row in rows
        ]

    async def top_deals(self, *, limit: int) -> list[NamedCount]:
        """Active deals ranked by discount percent then recency (proxy until deal-order analytics)."""
        stmt = (
            select(Deal.id, Deal.name, Deal.discount_percent)
            .where(Deal.deleted_at.is_(None), Deal.is_active.is_(True))
            .order_by(Deal.discount_percent.desc().nullslast(), Deal.updated_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            NamedCount(
                id=str(row.id),
                name=row.name,
                count=int(row.discount_percent or 0),
            )
            for row in rows
        ]
