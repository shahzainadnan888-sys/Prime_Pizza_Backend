"""Enterprise admin cross-entity search."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.catalog import Category, Product
from app.models.coupon import Coupon
from app.models.deal import Deal
from app.models.order import Order
from app.models.user import User
from app.schemas.admin_search import (
    AdminSearchHit,
    AdminSearchRequest,
    AdminSearchResponse,
    SearchEntity,
)
from app.services.base import BaseService


class AdminSearchService(BaseService):
    service_name = "admin_search"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def search(self, payload: AdminSearchRequest) -> AdminSearchResponse:
        q = payload.q.strip()
        entities: list[SearchEntity] = payload.entities or [
            "customers",
            "orders",
            "products",
            "coupons",
            "deals",
            "categories",
            "audit_logs",
        ]
        limit = payload.limit_per_entity
        pattern = f"%{q}%"
        results: list[AdminSearchHit] = []

        if "customers" in entities:
            rows = (
                await self._session.execute(
                    select(User)
                    .where(
                        User.deleted_at.is_(None),
                        or_(
                            User.full_name.ilike(pattern),
                            User.phone_number.ilike(pattern),
                            User.email.ilike(pattern),
                        ),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="customers",
                        id=str(row.id),
                        title=row.full_name or row.phone_number,
                        subtitle=row.phone_number,
                        meta={"role": row.role.value, "is_active": row.is_active},
                    )
                )

        if "orders" in entities:
            rows = (
                await self._session.execute(
                    select(Order)
                    .where(
                        Order.deleted_at.is_(None),
                        Order.order_number.ilike(pattern),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="orders",
                        id=str(row.id),
                        title=row.order_number,
                        subtitle=row.status.value,
                        meta={"grand_total": str(row.grand_total)},
                    )
                )

        if "products" in entities:
            rows = (
                await self._session.execute(
                    select(Product)
                    .where(
                        Product.deleted_at.is_(None),
                        or_(Product.name.ilike(pattern), Product.slug.ilike(pattern)),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="products",
                        id=str(row.id),
                        title=row.name,
                        subtitle=row.slug,
                    )
                )

        if "coupons" in entities:
            rows = (
                await self._session.execute(
                    select(Coupon)
                    .where(
                        Coupon.deleted_at.is_(None),
                        or_(Coupon.code.ilike(pattern), Coupon.description.ilike(pattern)),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="coupons",
                        id=str(row.id),
                        title=row.code,
                        subtitle=row.coupon_type.value,
                    )
                )

        if "deals" in entities:
            rows = (
                await self._session.execute(
                    select(Deal)
                    .where(
                        Deal.deleted_at.is_(None),
                        or_(Deal.name.ilike(pattern), Deal.slug.ilike(pattern)),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="deals",
                        id=str(row.id),
                        title=row.name,
                        subtitle=row.slug,
                    )
                )

        if "categories" in entities:
            rows = (
                await self._session.execute(
                    select(Category)
                    .where(
                        Category.deleted_at.is_(None),
                        or_(Category.name.ilike(pattern), Category.slug.ilike(pattern)),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="categories",
                        id=str(row.id),
                        title=row.name,
                        subtitle=row.slug,
                    )
                )

        if "audit_logs" in entities:
            rows = (
                await self._session.execute(
                    select(AuditLog)
                    .where(
                        AuditLog.deleted_at.is_(None),
                        or_(
                            AuditLog.message.ilike(pattern),
                            AuditLog.resource_type.ilike(pattern),
                            AuditLog.resource_id.ilike(pattern),
                        ),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            for row in rows:
                results.append(
                    AdminSearchHit(
                        entity="audit_logs",
                        id=str(row.id),
                        title=row.resource_type,
                        subtitle=row.message,
                        meta={"action": row.action.value},
                    )
                )

        return AdminSearchResponse(query=q, results=results, total_hits=len(results))
