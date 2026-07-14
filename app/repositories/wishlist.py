"""Wishlist repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wishlist import Wishlist, WishlistItem
from app.repositories.base import BaseRepository


class WishlistRepository(BaseRepository[Wishlist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Wishlist)

    async def get_for_user(self, user_id: UUID) -> Wishlist | None:
        stmt = (
            select(Wishlist)
            .where(Wishlist.user_id == user_id, Wishlist.deleted_at.is_(None))
            .options(selectinload(Wishlist.items).selectinload(WishlistItem.product))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class WishlistItemRepository(BaseRepository[WishlistItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WishlistItem)

    async def get_item(self, wishlist_id: UUID, product_id: UUID) -> WishlistItem | None:
        stmt = select(WishlistItem).where(
            WishlistItem.wishlist_id == wishlist_id,
            WishlistItem.product_id == product_id,
            WishlistItem.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_wishlist(self, wishlist_id: UUID) -> list[WishlistItem]:
        stmt = (
            select(WishlistItem)
            .where(WishlistItem.wishlist_id == wishlist_id, WishlistItem.deleted_at.is_(None))
            .options(selectinload(WishlistItem.product))
            .order_by(WishlistItem.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
