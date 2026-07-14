"""Checkout validation — readiness only, never creates an order."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import StockStatus
from app.config.settings import Settings
from app.core.exceptions import ValidationException
from app.models.user import User
from app.repositories.address import AddressRepository
from app.repositories.cart import CartRepository
from app.repositories.extra import ExtraOptionRepository, ProductOptionRepository
from app.repositories.product import ProductRepository
from app.repositories.variant import VariantRepository
from app.schemas.cart import CheckoutValidationIssue, CheckoutValidationResponse
from app.services.base import BaseService
from app.services.cart import CartService
from app.services.cart_cache import CartCacheService
from app.services.order_summary import OrderSummaryService


class CheckoutValidationService(BaseService):
    """Validate cart readiness for checkout without placing an order."""

    service_name = "checkout_validation"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        cart_service: CartService,
        summary: OrderSummaryService,
        cache: CartCacheService,
    ) -> None:
        self._session = session
        self._settings = settings
        self._carts = CartRepository(session)
        self._addresses = AddressRepository(session)
        self._products = ProductRepository(session)
        self._variants = VariantRepository(session)
        self._extras = ExtraOptionRepository(session)
        self._product_options = ProductOptionRepository(session)
        self._cart_service = cart_service
        self._summary = summary
        self._cache = cache

    async def validate(self, user: User, *, commit: bool = True) -> CheckoutValidationResponse:
        """
        Validate cart readiness for checkout.

        When ``commit=False`` (order placement), recalculation is flushed only so the
        caller retains a single atomic transaction boundary.
        """
        issues: list[CheckoutValidationIssue] = []

        if not user.is_verified:
            issues.append(
                CheckoutValidationIssue(
                    code="user_unverified",
                    message="Phone number must be verified",
                    field="user",
                )
            )
        if not user.is_active:
            issues.append(
                CheckoutValidationIssue(
                    code="user_inactive",
                    message="Account is inactive",
                    field="user",
                )
            )

        cart = await self._cart_service.get_or_create_cart(user)
        try:
            await self._cart_service.recalculate(cart)
            if commit:
                await self._session.commit()
        except ValidationException as exc:
            issues.append(
                CheckoutValidationIssue(code="pricing_error", message=str(exc.message), field="cart")
            )
            if commit:
                await self._session.rollback()
                cart = await self._cart_service.get_or_create_cart(user)
            else:
                raise

        cart = await self._carts.get_active_for_user(user.id)
        assert cart is not None
        active_items = [item for item in cart.items if item.deleted_at is None]
        if not active_items:
            issues.append(
                CheckoutValidationIssue(code="cart_empty", message="Cart is empty", field="cart")
            )

        for item in active_items:
            if item.quantity < self._settings.cart_min_item_quantity:
                issues.append(
                    CheckoutValidationIssue(
                        code="quantity_too_low",
                        message=f"Minimum quantity is {self._settings.cart_min_item_quantity}",
                        field=str(item.id),
                    )
                )
            if item.quantity > self._settings.cart_max_item_quantity:
                issues.append(
                    CheckoutValidationIssue(
                        code="quantity_too_high",
                        message=f"Maximum quantity is {self._settings.cart_max_item_quantity}",
                        field=str(item.id),
                    )
                )

            product = await self._products.get_detail(item.product_id, public_only=False)
            if product is None or not product.is_available or not product.is_visible:
                issues.append(
                    CheckoutValidationIssue(
                        code="product_unavailable",
                        message="A product in your cart is unavailable",
                        field=str(item.product_id),
                    )
                )
            elif product.stock_status == StockStatus.OUT_OF_STOCK:
                issues.append(
                    CheckoutValidationIssue(
                        code="product_out_of_stock",
                        message="A product in your cart is out of stock",
                        field=str(item.product_id),
                    )
                )

            if item.variant_id is not None:
                variants = await self._variants.list_for_product(item.product_id)
                variant = next((v for v in variants if v.id == item.variant_id), None)
                if variant is None or not variant.is_available:
                    issues.append(
                        CheckoutValidationIssue(
                            code="variant_unavailable",
                            message="A selected size/variant is unavailable",
                            field=str(item.variant_id),
                        )
                    )

            allowed_links = await self._product_options.list_for_product(item.product_id)
            allowed = {link.option_id for link in allowed_links}
            for extra in item.extras:
                if extra.deleted_at is not None:
                    continue
                options = await self._extras.get_by_ids([extra.option_id])
                option = options[0] if options else None
                if option is None or not option.is_available or extra.option_id not in allowed:
                    issues.append(
                        CheckoutValidationIssue(
                            code="extra_unavailable",
                            message="A selected extra/topping is unavailable",
                            field=str(extra.option_id),
                        )
                    )

        if cart.coupon_id and cart.coupon is not None:
            from app.services.coupon import CouponService

            coupon_service = CouponService(session=self._session)
            try:
                await coupon_service.validate_for_user(
                    code=cart.coupon.code,
                    user_id=user.id,
                    subtotal=cart.subtotal,
                )
            except Exception as exc:
                issues.append(
                    CheckoutValidationIssue(
                        code="coupon_invalid",
                        message=getattr(exc, "message", str(exc)),
                        field="coupon",
                    )
                )

        addresses = await self._addresses.list_for_user(user.id)
        has_default = any(addr.is_default for addr in addresses)
        if not addresses:
            issues.append(
                CheckoutValidationIssue(
                    code="address_missing",
                    message="Add a delivery address before checkout",
                    field="address",
                )
            )
        elif not has_default:
            issues.append(
                CheckoutValidationIssue(
                    code="default_address_missing",
                    message="Set a default delivery address before checkout",
                    field="address",
                )
            )

        summary = None
        is_valid = len(issues) == 0
        if is_valid:
            summary = self._summary.build(cart)
            cart.status = cart.status  # no order created
            await self._cache.set_json(
                self._cache.checkout_key(user.id),
                summary.model_dump(mode="json"),
            )

        logger.info(
            "Checkout validation | user_id={} | valid={} | issues={}",
            user.id,
            is_valid,
            len(issues),
        )
        return CheckoutValidationResponse(
            is_valid=is_valid,
            issues=issues,
            summary=summary,
            has_default_address=has_default,
            address_count=len(addresses),
        )
