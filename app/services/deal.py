"""Deal service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.deal import Deal, DealProduct
from app.repositories.deal import DealProductRepository, DealRepository
from app.repositories.product import ProductRepository
from app.schemas.catalog import DealCreateRequest, DealResponse, DealUpdateRequest
from app.services.base import BaseService
from app.services.catalog_cache import CatalogCacheService
from app.services.catalog_mapper import to_deal_response
from app.utils.slug import slugify


class DealService(BaseService):
    service_name = "deal"

    def __init__(
        self,
        *,
        session: AsyncSession,
        cache: CatalogCacheService,
    ) -> None:
        self._session = session
        self._deals = DealRepository(session)
        self._deal_products = DealProductRepository(session)
        self._products = ProductRepository(session)
        self._cache = cache

    async def list_public(self) -> list[DealResponse]:
        cached = await self._cache.get_json(self._cache.deals_key())
        if cached is not None:
            return [DealResponse.model_validate(item) for item in cached]
        rows = await self._deals.list_public()
        data = [to_deal_response(row) for row in rows]
        await self._cache.set_json(
            self._cache.deals_key(),
            [item.model_dump(mode="json") for item in data],
        )
        return data

    async def get_by_slug(self, slug: str) -> DealResponse:
        deal = await self._deals.get_by_slug(slug, public_only=True)
        if deal is None:
            raise NotFoundException("Deal not found")
        return to_deal_response(deal)

    async def _sync_products(self, deal_id: UUID, items: list) -> None:
        await self._deal_products.soft_delete_for_deal(deal_id)
        seen: set[UUID] = set()
        for item in items:
            if item.product_id in seen:
                raise ValidationException("Duplicate product in deal")
            seen.add(item.product_id)
            product = await self._products.get_by_id(item.product_id)
            if product is None:
                raise NotFoundException("Product not found for deal")
            await self._deal_products.add(
                DealProduct(deal_id=deal_id, product_id=item.product_id, quantity=item.quantity)
            )

    async def create(self, payload: DealCreateRequest) -> DealResponse:
        slug = payload.slug or slugify(payload.name, max_length=220)
        if await self._deals.slug_exists(slug):
            raise ConflictException("Deal slug already exists")
        deal = Deal(
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            deal_type=payload.deal_type,
            deal_price=payload.deal_price,
            discount_percent=payload.discount_percent,
            image_url=payload.image_url,
            is_active=payload.is_active,
            is_visible=payload.is_visible,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
        await self._deals.add(deal)
        await self._session.flush()
        await self._sync_products(deal.id, payload.products)
        await self._session.commit()
        detail = await self._deals.get_detail(deal.id)
        assert detail is not None
        await self._cache.invalidate_all()
        logger.info("Deal created | deal_id={} | slug={}", deal.id, deal.slug)
        return to_deal_response(detail)

    async def update(self, deal_id: UUID, payload: DealUpdateRequest) -> DealResponse:
        deal = await self._deals.get_by_id(deal_id)
        if deal is None:
            raise NotFoundException("Deal not found")
        data = payload.model_dump(exclude_unset=True, exclude={"products"})
        if not data and payload.products is None:
            raise ValidationException("No deal fields provided")
        if "slug" in data and data["slug"] and await self._deals.slug_exists(
            data["slug"],
            exclude_id=deal_id,
        ):
            raise ConflictException("Deal slug already exists")
        if "name" in data and data["name"]:
            data["name"] = str(data["name"]).strip()
        for key, value in data.items():
            setattr(deal, key, value)
        if payload.products is not None:
            await self._sync_products(deal_id, payload.products)
        await self._session.commit()
        detail = await self._deals.get_detail(deal_id)
        assert detail is not None
        await self._cache.invalidate_all()
        logger.info("Deal updated | deal_id={}", deal_id)
        return to_deal_response(detail)

    async def delete(self, deal_id: UUID) -> None:
        deal = await self._deals.get_by_id(deal_id)
        if deal is None:
            raise NotFoundException("Deal not found")
        await self._deals.soft_delete(deal)
        await self._session.commit()
        await self._cache.invalidate_all()
        logger.info("Deal deleted | deal_id={}", deal_id)

    async def set_active(self, deal_id: UUID, *, is_active: bool) -> DealResponse:
        return await self.update(deal_id, DealUpdateRequest(is_active=is_active))

    async def schedule(
        self,
        deal_id: UUID,
        *,
        starts_at=None,
        ends_at=None,
        is_active: bool | None = None,
        is_visible: bool | None = None,
    ) -> DealResponse:
        return await self.update(
            deal_id,
            DealUpdateRequest(
                starts_at=starts_at,
                ends_at=ends_at,
                is_active=is_active,
                is_visible=is_visible,
            ),
        )
