"""Address repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Address)

    async def list_for_user(self, user_id: UUID) -> list[Address]:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id, Address.deleted_at.is_(None))
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, address_id: UUID, user_id: UUID) -> Address | None:
        stmt = select(Address).where(
            Address.id == address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_for_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Address).where(
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def clear_defaults(self, user_id: UUID) -> None:
        stmt = (
            update(Address)
            .where(
                Address.user_id == user_id,
                Address.deleted_at.is_(None),
                Address.is_default.is_(True),
            )
            .values(is_default=False)
        )
        await self.session.execute(stmt)
