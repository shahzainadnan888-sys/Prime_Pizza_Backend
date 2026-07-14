"""Wishlist service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.user import User
from app.models.wishlist import Wishlist, WishlistItem
from app.repositories.product import ProductRepository
from app.repositories.wishlist import WishlistItemRepository, WishlistRepository
from app.schemas.cart import WishlistItemResponse, WishlistResponse
from app.services.base import BaseService


class WishlistService(BaseService):
    service_name = "wishlist"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session
        self._wishlists = WishlistRepository(session)
        self._items = WishlistItemRepository(session)
        self._products = ProductRepository(session)

    async def get_or_create(self, user: User) -> Wishlist:
        wishlist = await self._wishlists.get_for_user(user.id)
        if wishlist is not None:
            return wishlist
        wishlist = Wishlist(user_id=user.id)
        await self._wishlists.add(wishlist)
        await self._session.commit()
        created = await self._wishlists.get_for_user(user.id)
        assert created is not None
        return created

    def _to_response(self, wishlist: Wishlist) -> WishlistResponse:
        items = []
        for item in wishlist.items:
            if item.deleted_at is not None:
                continue
            product = item.product
            items.append(
                WishlistItemResponse(
                    product_id=item.product_id,
                    product_name=product.name if product else None,
                    product_slug=product.slug if product else None,
                    image_url=product.image_url if product else None,
                    base_price=product.base_price if product else None,
                    is_available=product.is_available if product else None,
                    added_at=item.created_at,
                )
            )
        return WishlistResponse(id=wishlist.id, item_count=len(items), items=items)

    async def list_wishlist(self, user: User) -> WishlistResponse:
        wishlist = await self.get_or_create(user)
        return self._to_response(wishlist)

    async def add(self, user: User, product_id: UUID) -> WishlistResponse:
        product = await self._products.get_by_id(product_id)
        if product is None or product.deleted_at is not None:
            raise NotFoundException("Product not found")
        wishlist = await self.get_or_create(user)
        existing = await self._items.get_item(wishlist.id, product_id)
        if existing is not None:
            raise ConflictException("Product already in wishlist")
        await self._items.add(WishlistItem(wishlist_id=wishlist.id, product_id=product_id))
        await self._session.commit()
        logger.info("Wishlist added | user_id={} | product_id={}", user.id, product_id)
        return self._to_response(await self.get_or_create(user))

    async def remove(self, user: User, product_id: UUID) -> WishlistResponse:
        wishlist = await self.get_or_create(user)
        item = await self._items.get_item(wishlist.id, product_id)
        if item is None:
            raise NotFoundException("Wishlist item not found")
        await self._items.soft_delete(item)
        await self._session.commit()
        logger.info("Wishlist removed | user_id={} | product_id={}", user.id, product_id)
        return self._to_response(await self.get_or_create(user))

    async def clear(self, user: User) -> WishlistResponse:
        wishlist = await self.get_or_create(user)
        for item in list(wishlist.items):
            if item.deleted_at is None:
                await self._items.soft_delete(item)
        await self._session.commit()
        logger.info("Wishlist cleared | user_id={}", user.id)
        return self._to_response(await self.get_or_create(user))
