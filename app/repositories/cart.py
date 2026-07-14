"""Cart and cart-item repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem, CartItemExtra
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cart)

    async def get_active_for_user(self, user_id: UUID) -> Cart | None:
        stmt = (
            select(Cart)
            .where(
                Cart.user_id == user_id,
                Cart.is_active.is_(True),
                Cart.deleted_at.is_(None),
            )
            .options(
                selectinload(Cart.items).selectinload(CartItem.extras).selectinload(CartItemExtra.option),
                selectinload(Cart.items).selectinload(CartItem.product),
                selectinload(Cart.items).selectinload(CartItem.variant),
                selectinload(Cart.coupon),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_for_update(self, user_id: UUID) -> Cart | None:
        """Load active cart with row lock to reduce race conditions."""
        stmt = (
            select(Cart)
            .where(
                Cart.user_id == user_id,
                Cart.is_active.is_(True),
                Cart.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class CartItemRepository(BaseRepository[CartItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CartItem)

    async def get_for_cart(self, cart_id: UUID, item_id: UUID) -> CartItem | None:
        stmt = (
            select(CartItem)
            .where(
                CartItem.id == item_id,
                CartItem.cart_id == cart_id,
                CartItem.deleted_at.is_(None),
            )
            .options(
                selectinload(CartItem.extras),
                selectinload(CartItem.product),
                selectinload(CartItem.variant),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_cart(self, cart_id: UUID) -> list[CartItem]:
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id, CartItem.deleted_at.is_(None))
            .options(selectinload(CartItem.extras))
            .order_by(CartItem.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())


class CartItemExtraRepository(BaseRepository[CartItemExtra]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CartItemExtra)

    async def soft_delete_for_item(self, cart_item_id: UUID) -> None:
        stmt = select(CartItemExtra).where(
            CartItemExtra.cart_item_id == cart_item_id,
            CartItemExtra.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        for row in result.scalars().all():
            await self.soft_delete(row)
