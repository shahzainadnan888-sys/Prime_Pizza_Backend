"""Owner customer management service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction, UserRole
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.repositories.user import UserRepository
from app.schemas.admin_customers import (
    AdminCustomerDetailResponse,
    AdminCustomerFilterParams,
    AdminCustomerStatusRequest,
    AdminCustomerUpdateRequest,
)
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.schemas.users import UserProfileResponse
from app.services.audit import AuditService
from app.services.base import BaseService
from app.services.dashboard_cache import DashboardCacheService


class AdminCustomerService(BaseService):
    service_name = "admin_customer"

    def __init__(
        self,
        *,
        session: AsyncSession,
        audit: AuditService,
        dashboard_cache: DashboardCacheService,
    ) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._audit = audit
        self._dashboard_cache = dashboard_cache

    def _to_profile(self, user) -> UserProfileResponse:
        return UserProfileResponse.model_validate(user)

    async def list_customers(
        self,
        filters: AdminCustomerFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[UserProfileResponse], PaginationMeta]:
        rows, total = await self._users.list_admin_filtered(
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [self._to_profile(row) for row in rows], meta

    async def get_customer(self, customer_id: UUID) -> AdminCustomerDetailResponse:
        user = await self._users.get_by_id(customer_id)
        if user is None or user.role != UserRole.CUSTOMER:
            raise NotFoundException("Customer not found")
        order_count = await self._users.count_orders_for_user(user.id)
        base = self._to_profile(user)
        return AdminCustomerDetailResponse(
            **base.model_dump(),
            updated_at=user.updated_at,
            order_count=order_count,
        )

    async def update_customer(
        self,
        customer_id: UUID,
        payload: AdminCustomerUpdateRequest,
        *,
        actor_id: UUID,
    ) -> AdminCustomerDetailResponse:
        user = await self._users.get_by_id(customer_id)
        if user is None or user.role != UserRole.CUSTOMER:
            raise NotFoundException("Customer not found")
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No customer fields provided")
        if "role" in data:
            raise ValidationException("Role changes are not allowed via this endpoint")
        if "email" in data and data["email"] is not None:
            existing = await self._users.get_by_email(str(data["email"]))
            if existing is not None and existing.id != customer_id:
                raise ConflictException("Email already in use")
            data["email"] = str(data["email"])
        for key, value in data.items():
            setattr(user, key, value)
        await self._session.commit()
        await self._audit.record(
            action=AuditAction.UPDATE,
            resource_type="customer",
            resource_id=str(customer_id),
            user_id=actor_id,
            message="Customer updated",
            details={"fields": list(data.keys())},
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        logger.info("Customer updated | customer_id={} | by={}", customer_id, actor_id)
        return await self.get_customer(customer_id)

    async def update_status(
        self,
        customer_id: UUID,
        payload: AdminCustomerStatusRequest,
        *,
        actor_id: UUID,
    ) -> AdminCustomerDetailResponse:
        user = await self._users.get_by_id(customer_id)
        if user is None or user.role != UserRole.CUSTOMER:
            raise NotFoundException("Customer not found")
        user.is_active = payload.is_active
        await self._session.commit()
        await self._audit.record(
            action=AuditAction.UPDATE,
            resource_type="customer",
            resource_id=str(customer_id),
            user_id=actor_id,
            message="Customer status updated",
            details={"is_active": payload.is_active},
            commit=True,
        )
        await self._dashboard_cache.invalidate_all()
        logger.info(
            "Customer status updated | customer_id={} | active={}",
            customer_id,
            payload.is_active,
        )
        return await self.get_customer(customer_id)
