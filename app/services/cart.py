"""Cart service — authoritative DB pricing, no client-trusted amounts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import CartStatus, StockStatus
from app.config.settings import Settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.cart import Cart, CartItem, CartItemExtra
from app.models.catalog import Product, ProductVariant, VariantOption
from app.models.user import User
from app.repositories.cart import CartItemExtraRepository, CartItemRepository, CartRepository
from app.repositories.extra import ExtraOptionRepository, ProductOptionRepository
from app.repositories.product import ProductRepository
from app.repositories.variant import VariantRepository
from app.schemas.cart import (
    AddCartItemRequest,
    ApplyCouponRequest,
    CartItemExtraResponse,
    CartItemResponse,
    CartResponse,
    OrderSummaryResponse,
    UpdateCartItemRequest,
)
from app.services.base import BaseService
from app.services.cart_cache import CartCacheService
from app.services.commerce_config import CommerceConfigService
from app.services.coupon import CouponService
from app.services.delivery import DeliveryService
from app.services.order_summary import OrderSummaryService
from app.services.pricing import PricingService, money
from app.services.tax import TaxService


class CartService(BaseService):
    service_name = "cart"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        cache: CartCacheService,
        pricing: PricingService,
        delivery: DeliveryService,
        tax: TaxService,
        coupon: CouponService,
        summary: OrderSummaryService,
        commerce: CommerceConfigService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._cache = cache
        self._pricing = pricing
        self._delivery = delivery
        self._tax = tax
        self._coupon = coupon
        self._summary = summary
        self._commerce = commerce
        self._carts = CartRepository(session)
        self._items = CartItemRepository(session)
        self._item_extras = CartItemExtraRepository(session)
        self._products = ProductRepository(session)
        self._variants = VariantRepository(session)
        self._extras = ExtraOptionRepository(session)
        self._product_options = ProductOptionRepository(session)

    async def get_or_create_cart(self, user: User) -> Cart:
        cart = await self._carts.get_active_for_user(user.id)
        if cart is not None:
            return cart
        cart = Cart(
            user_id=user.id,
            is_active=True,
            status=CartStatus.ACTIVE,
            currency="PKR",
            last_activity=datetime.now(UTC),
        )
        await self._carts.add(cart)
        await self._session.commit()
        return await self._require_cart(user.id)

    async def _require_cart(self, user_id: UUID) -> Cart:
        cart = await self._carts.get_active_for_user(user_id)
        if cart is None:
            raise NotFoundException("Cart not found")
        return cart

    def _to_response(self, cart: Cart) -> CartResponse:
        items = []
        for item in cart.items:
            if item.deleted_at is not None:
                continue
            extras = [
                CartItemExtraResponse(
                    option_id=extra.option_id,
                    name=extra.option.name if extra.option else None,
                    quantity=extra.quantity,
                    unit_price=extra.unit_price,
                )
                for extra in item.extras
                if extra.deleted_at is None
            ]
            items.append(
                CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product.name if item.product else None,
                    product_slug=item.product.slug if item.product else None,
                    image_url=item.product.image_url if item.product else None,
                    variant_id=item.variant_id,
                    variant_name=item.variant.name if item.variant else None,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_price=item.discount_price,
                    subtotal=item.subtotal,
                    special_instructions=item.special_instructions,
                    extras=extras,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )
        return CartResponse(
            id=cart.id,
            status=cart.status,
            currency=cart.currency,
            notes=cart.notes,
            last_activity=cart.last_activity,
            coupon_id=cart.coupon_id,
            coupon_code=cart.coupon.code if cart.coupon else None,
            subtotal=cart.subtotal,
            discount=cart.discount,
            delivery_fee=cart.delivery_fee,
            tax=cart.tax,
            grand_total=cart.grand_total,
            item_count=sum(i.quantity for i in items),
            items=items,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    async def get_cart(self, user: User) -> CartResponse:
        """
        Return the active cart quickly from stored line totals.

        Full catalog recalculation runs on mutations (add/update/remove/coupon)
        and checkout — not on every GET — to avoid Neon N+1 latency timeouts.
        """
        cart = await self.get_or_create_cart(user)
        return self._to_response(cart)

    async def get_summary(self, user: User) -> OrderSummaryResponse:
        cached = await self._cache.get_json(self._cache.summary_key(user.id))
        if cached is not None:
            return OrderSummaryResponse.model_validate(cached)
        cart = await self.get_or_create_cart(user)
        # Use stored totals for a fast summary; mutations keep totals authoritative.
        summary = self._summary.build(cart)
        await self._cache.set_json(self._cache.summary_key(user.id), summary.model_dump(mode="json"))
        return summary

    async def _load_priced_entities(
        self,
        *,
        product_id: UUID,
        variant_id: UUID | None,
        option_ids: list[UUID],
        extra_quantities: dict[UUID, int] | None = None,
        require_available: bool = True,
    ) -> tuple[Product, ProductVariant | None, list[tuple[VariantOption, int]]]:
        product = await self._products.get_detail(product_id, public_only=False)
        if product is None or product.deleted_at is not None:
            raise NotFoundException("Product not found")
        if require_available:
            if not product.is_available or not product.is_visible:
                raise ValidationException("Product is not available")
            if product.stock_status == StockStatus.OUT_OF_STOCK:
                raise ValidationException("Product is out of stock")

        variant: ProductVariant | None = None
        if variant_id is not None:
            variants = await self._variants.list_for_product(product_id)
            variant = next((v for v in variants if v.id == variant_id), None)
            if variant is None:
                raise NotFoundException("Variant not found for product")
            if require_available and not variant.is_available:
                raise ValidationException("Variant is not available")

        extras: list[tuple[VariantOption, int]] = []
        if option_ids:
            options = await self._extras.get_by_ids(option_ids)
            by_id = {o.id: o for o in options}
            allowed = await self._product_options.list_for_product(product_id)
            allowed_ids = {link.option_id for link in allowed}
            for option_id in option_ids:
                option = by_id.get(option_id)
                if option is None:
                    raise NotFoundException("Extra option not found")
                if require_available and option_id not in allowed_ids:
                    raise ValidationException("Extra is not available for this product")
                if require_available and not option.is_available:
                    raise ValidationException(f"Extra '{option.name}' is not available")
                qty = (extra_quantities or {}).get(option_id, 1)
                extras.append((option, qty))
        return product, variant, extras

    def _normalize_extras(
        self,
        payload: AddCartItemRequest | UpdateCartItemRequest,
    ) -> tuple[list[UUID], dict[UUID, int]]:
        quantities: dict[UUID, int] = {}
        if getattr(payload, "extras", None):
            for item in payload.extras or []:
                quantities[item.option_id] = quantities.get(item.option_id, 0) + item.quantity
        ids = list(getattr(payload, "extra_option_ids", None) or [])
        for option_id in ids:
            quantities.setdefault(option_id, 1)
        return list(quantities.keys()), quantities

    def _extras_signature(self, extras: list[tuple[VariantOption, int]]) -> tuple[tuple[str, int], ...]:
        return tuple(sorted((str(option.id), qty) for option, qty in extras))

    async def _find_matching_item(
        self,
        cart: Cart,
        *,
        product_id: UUID,
        variant_id: UUID | None,
        signature: tuple[tuple[str, int], ...],
    ) -> CartItem | None:
        for item in cart.items:
            if item.deleted_at is not None:
                continue
            if item.product_id != product_id or item.variant_id != variant_id:
                continue
            current = tuple(
                sorted(
                    (str(extra.option_id), extra.quantity)
                    for extra in item.extras
                    if extra.deleted_at is None
                )
            )
            if current == signature:
                return item
        return None

    def _validate_quantity(self, quantity: int) -> None:
        if quantity < self._settings.cart_min_item_quantity:
            raise ValidationException(f"Minimum quantity is {self._settings.cart_min_item_quantity}")
        if quantity > self._settings.cart_max_item_quantity:
            raise ValidationException(f"Maximum quantity is {self._settings.cart_max_item_quantity}")

    async def recalculate(self, cart: Cart) -> None:
        """Recompute all cart totals from PostgreSQL catalog prices."""
        active_items = [item for item in cart.items if item.deleted_at is None]
        line_totals = []
        for item in active_items:
            product, variant, extras = await self._load_priced_entities(
                product_id=item.product_id,
                variant_id=item.variant_id,
                option_ids=[e.option_id for e in item.extras if e.deleted_at is None],
                extra_quantities={e.option_id: e.quantity for e in item.extras if e.deleted_at is None},
                require_available=False,
            )
            priced = self._pricing.price_line(
                product=product,
                variant=variant,
                quantity=item.quantity,
                extras=extras,
            )
            item.unit_price = priced.unit_price
            item.discount_price = priced.discount_price
            item.subtotal = priced.line_subtotal
            item.extras_snapshot = [
                {
                    "option_id": str(option.id),
                    "name": option.name,
                    "quantity": qty,
                    "unit_price": str(money(option.price)),
                }
                for option, qty in extras
            ]
            for extra in item.extras:
                if extra.deleted_at is None:
                    option = next(o for o, _ in extras if o.id == extra.option_id)
                    extra.unit_price = money(option.price)
            line_totals.append(priced.line_subtotal)

        subtotal = self._pricing.cart_subtotal(line_totals)
        discount = money(0)
        if cart.coupon_id and cart.coupon is not None:
            try:
                validation = await self._coupon.validate_for_user(
                    code=cart.coupon.code,
                    user_id=cart.user_id,
                    subtotal=subtotal,
                )
                discount = validation.discount_amount
            except (ValidationException, NotFoundException):
                cart.coupon_id = None
                discount = money(0)

        after_discount = money(subtotal - discount)
        commerce = await self._commerce.get()
        delivery_fee = self._delivery.calculate_fee(
            subtotal_after_discount=after_discount,
            commerce=commerce,
        )
        tax = self._tax.calculate(taxable_amount=after_discount, commerce=commerce)
        cart.subtotal = subtotal
        cart.discount = discount
        cart.delivery_fee = delivery_fee
        cart.tax = tax
        cart.grand_total = money(after_discount + delivery_fee + tax)
        cart.last_activity = datetime.now(UTC)
        await self._session.flush()

    async def add_item(self, user: User, payload: AddCartItemRequest) -> CartResponse:
        self._validate_quantity(payload.quantity)
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        option_ids, quantities = self._normalize_extras(payload)
        product, variant, extras = await self._load_priced_entities(
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            option_ids=option_ids,
            extra_quantities=quantities,
        )
        signature = self._extras_signature(extras)
        existing = await self._find_matching_item(
            cart,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            signature=signature,
        )
        if existing is not None:
            new_qty = existing.quantity + payload.quantity
            self._validate_quantity(new_qty)
            existing.quantity = new_qty
            if payload.special_instructions is not None:
                existing.special_instructions = payload.special_instructions
        else:
            active_count = sum(1 for i in cart.items if i.deleted_at is None)
            if active_count >= self._settings.cart_max_items:
                raise ValidationException(f"Cart may contain at most {self._settings.cart_max_items} items")
            priced = self._pricing.price_line(
                product=product,
                variant=variant,
                quantity=payload.quantity,
                extras=extras,
            )
            item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                quantity=payload.quantity,
                unit_price=priced.unit_price,
                discount_price=priced.discount_price,
                subtotal=priced.line_subtotal,
                special_instructions=payload.special_instructions,
                extras_snapshot=[],
            )
            await self._items.add(item)
            await self._session.flush()
            for option, qty in extras:
                await self._item_extras.add(
                    CartItemExtra(
                        cart_item_id=item.id,
                        option_id=option.id,
                        quantity=qty,
                        unit_price=money(option.price),
                    )
                )

        cart = await self._require_cart(user.id)
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        logger.info("Product added to cart | user_id={} | product_id={}", user.id, payload.product_id)
        return self._to_response(await self._require_cart(user.id))

    async def update_item(
        self,
        user: User,
        item_id: UUID,
        payload: UpdateCartItemRequest,
    ) -> CartResponse:
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        item = await self._items.get_for_cart(cart.id, item_id)
        if item is None:
            raise NotFoundException("Cart item not found")

        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No cart item fields provided")

        if payload.quantity is not None:
            self._validate_quantity(payload.quantity)
            item.quantity = payload.quantity
        if "special_instructions" in payload.model_fields_set:
            item.special_instructions = payload.special_instructions

        if payload.extra_option_ids is not None or payload.extras is not None:
            option_ids, quantities = self._normalize_extras(payload)
            product, variant, extras = await self._load_priced_entities(
                product_id=item.product_id,
                variant_id=item.variant_id,
                option_ids=option_ids,
                extra_quantities=quantities,
            )
            await self._item_extras.soft_delete_for_item(item.id)
            for option, qty in extras:
                await self._item_extras.add(
                    CartItemExtra(
                        cart_item_id=item.id,
                        option_id=option.id,
                        quantity=qty,
                        unit_price=money(option.price),
                    )
                )
            _ = product, variant

        cart = await self._require_cart(user.id)
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        logger.info("Quantity updated | user_id={} | item_id={}", user.id, item_id)
        return self._to_response(await self._require_cart(user.id))

    async def remove_item(self, user: User, item_id: UUID) -> CartResponse:
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        item = await self._items.get_for_cart(cart.id, item_id)
        if item is None:
            raise NotFoundException("Cart item not found")
        await self._items.soft_delete(item)
        cart = await self._require_cart(user.id)
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        logger.info("Product removed from cart | user_id={} | item_id={}", user.id, item_id)
        return self._to_response(await self._require_cart(user.id))

    async def clear(self, user: User) -> CartResponse:
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        for item in list(cart.items):
            if item.deleted_at is None:
                await self._items.soft_delete(item)
        cart.coupon_id = None
        cart = await self._require_cart(user.id)
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        logger.info("Cart cleared | user_id={}", user.id)
        return self._to_response(await self._require_cart(user.id))

    async def convert_cart_after_order(self, cart: Cart) -> None:
        """
        Soft-clear cart items and mark cart converted inside an open transaction.

        Does not commit — caller owns the transaction boundary.
        """
        for item in list(cart.items):
            if item.deleted_at is None:
                await self._items.soft_delete(item)
        cart.coupon_id = None
        cart.status = CartStatus.CONVERTED
        cart.is_active = False
        cart.last_activity = datetime.now(UTC)
        await self._session.flush()
        await self._cache.invalidate_user(cart.user_id)

    async def apply_coupon(self, user: User, payload: ApplyCouponRequest) -> CartResponse:
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        await self.recalculate(cart)
        validation = await self._coupon.validate_for_user(
            code=payload.code,
            user_id=user.id,
            subtotal=cart.subtotal,
        )
        coupon = await self._coupon.get_active_by_code(validation.code)
        cart.coupon_id = coupon.id
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        await self._cache.invalidate_coupon(validation.code)
        logger.info("Coupon applied | user_id={} | code={}", user.id, validation.code)
        return self._to_response(await self._require_cart(user.id))

    async def remove_coupon(self, user: User) -> CartResponse:
        await self._carts.get_active_for_update(user.id)
        cart = await self.get_or_create_cart(user)
        cart.coupon_id = None
        await self.recalculate(cart)
        await self._session.commit()
        await self._cache.invalidate_user(user.id)
        logger.info("Coupon removed | user_id={}", user.id)
        return self._to_response(await self._require_cart(user.id))
