"""Variant and extras orchestration for products."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.catalog import ProductOption, ProductVariant
from app.repositories.extra import ExtraOptionRepository, ProductOptionRepository
from app.repositories.variant import VariantRepository
from app.schemas.catalog import VariantCreateRequest
from app.services.base import BaseService


class VariantService(BaseService):
    service_name = "variant"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session
        self._variants = VariantRepository(session)
        self._extras = ExtraOptionRepository(session)
        self._product_options = ProductOptionRepository(session)

    async def replace_variants(self, product_id: UUID, variants: list[VariantCreateRequest]) -> None:
        await self._variants.soft_delete_for_product(product_id)
        sizes: set[str] = set()
        for item in variants:
            if item.size.value in sizes:
                raise ValidationException(f"Duplicate variant size: {item.size.value}")
            sizes.add(item.size.value)
            await self._variants.add(
                ProductVariant(
                    product_id=product_id,
                    size=item.size,
                    name=item.name,
                    price=item.price,
                    discount_price=item.discount_price,
                    preparation_time_minutes=item.preparation_time_minutes,
                    is_available=item.is_available,
                    display_order=item.display_order,
                )
            )

    async def replace_extras(self, product_id: UUID, option_ids: list[UUID]) -> None:
        await self._product_options.soft_delete_for_product(product_id)
        if not option_ids:
            return
        options = await self._extras.get_by_ids(option_ids)
        found = {option.id for option in options}
        missing = [str(oid) for oid in option_ids if oid not in found]
        if missing:
            raise NotFoundException("One or more extras were not found", details={"ids": missing})
        for option_id in option_ids:
            await self._product_options.add(
                ProductOption(product_id=product_id, option_id=option_id, is_default=False)
            )
