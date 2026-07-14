"""Order placement, history, tracking, and owner management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.ownership import OwnershipService
from app.common.enums import CartStatus, OrderStatus, PaymentMethod, PaymentStatus
from app.config.settings import Settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.coupon import CouponUsage
from app.models.order import Order, OrderItem, OrderItemExtra, OrderTimelineEvent
from app.models.user import Address, User
from app.repositories.address import AddressRepository
from app.repositories.cart import CartRepository
from app.repositories.coupon import CouponRepository, CouponUsageRepository
from app.repositories.order import OrderNumberSequenceRepository, OrderRepository, OrderTimelineRepository
from app.schemas.orders import (
    CancelOrderRequest,
    OrderDetailResponse,
    OrderFilterParams,
    OrderItemExtraResponse,
    OrderItemResponse,
    OrderListItemResponse,
    OrderTimelineEventResponse,
    OrderTrackingResponse,
    PlaceOrderRequest,
    UpdateOrderNotesRequest,
    UpdateOrderStatusRequest,
    UpdatePaymentStatusRequest,
)
from app.schemas.pagination import PaginationMeta, PaginationParams
from app.services.base import BaseService
from app.services.cart import CartService
from app.services.cart_cache import CartCacheService
from app.services.checkout import CheckoutValidationService
from app.services.coupon import CouponService
from app.services.dashboard_cache import DashboardCacheService
from app.services.email import EmailService
from app.services.order_cache import OrderCacheService
from app.services.order_email import build_order_email_payload
from app.services.order_summary import OrderSummaryService

STATUS_TITLES: dict[OrderStatus, str] = {
    OrderStatus.PENDING: "Order Created",
    OrderStatus.CONFIRMED: "Order Confirmed",
    OrderStatus.PREPARING: "Preparing",
    OrderStatus.READY: "Ready",
    OrderStatus.OUT_FOR_DELIVERY: "Out for Delivery",
    OrderStatus.DELIVERED: "Delivered",
    OrderStatus.CANCELLED: "Cancelled",
    OrderStatus.REFUNDED: "Refunded",
}

CUSTOMER_CANCELABLE = {OrderStatus.PENDING, OrderStatus.CONFIRMED}

# Allowed owner status transitions (prevents illegal jumps / replay of terminal states).
ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: {OrderStatus.REFUNDED},
    OrderStatus.REFUNDED: set(),
}


class OrderService(BaseService):
    service_name = "order"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        cart_service: CartService,
        checkout_validation: CheckoutValidationService,
        coupon_service: CouponService,
        summary_service: OrderSummaryService,
        order_cache: OrderCacheService,
        cart_cache: CartCacheService,
        email_service: EmailService | None = None,
        dashboard_cache: DashboardCacheService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._cart_service = cart_service
        self._checkout = checkout_validation
        self._coupons = coupon_service
        self._summary = summary_service
        self._cache = order_cache
        self._cart_cache = cart_cache
        self._email = email_service
        self._dashboard_cache = dashboard_cache
        self._orders = OrderRepository(session)
        self._timeline = OrderTimelineRepository(session)
        self._sequences = OrderNumberSequenceRepository(session)
        self._carts = CartRepository(session)
        self._addresses = AddressRepository(session)
        self._coupon_rows = CouponRepository(session)
        self._coupon_usages = CouponUsageRepository(session)
        self._ownership = OwnershipService()

    async def _invalidate_dashboard(self) -> None:
        if self._dashboard_cache is None:
            return
        try:
            await self._dashboard_cache.invalidate_all()
        except Exception:
            logger.exception("Dashboard cache invalidate failed after order mutation")

    async def _next_order_number(self) -> str:
        year = datetime.now(UTC).year
        seq = await self._sequences.next_value(year)
        return f"PP-{year}-{seq:06d}"

    async def _add_timeline(
        self,
        order: Order,
        *,
        status: OrderStatus,
        performed_by: UUID | None,
        notes: str | None = None,
    ) -> None:
        await self._timeline.add(
            OrderTimelineEvent(
                order_id=order.id,
                status=status,
                title=STATUS_TITLES.get(status, status.value),
                notes=notes,
                performed_by=performed_by,
            )
        )

    def _address_snapshot(self, address: Address) -> dict:
        return {
            "id": str(address.id),
            "title": address.title,
            "recipient_name": address.recipient_name,
            "phone_number": address.phone_number,
            "street": address.street,
            "area": address.area,
            "city": address.city,
            "province": address.province,
            "postal_code": address.postal_code,
            "country": address.country,
            "latitude": str(address.latitude) if address.latitude is not None else None,
            "longitude": str(address.longitude) if address.longitude is not None else None,
            "delivery_notes": address.delivery_notes,
        }

    def _to_item_response(self, item: OrderItem) -> OrderItemResponse:
        extras = [
            OrderItemExtraResponse.model_validate(extra)
            for extra in item.extras
            if extra.deleted_at is None
        ]
        return OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            product_slug=item.product_slug,
            variant_id=item.variant_id,
            variant_name=item.variant_name,
            variant_size=item.variant_size,
            image_url=item.image_url,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_price=item.discount_price,
            subtotal=item.subtotal,
            preparation_time_minutes=item.preparation_time_minutes,
            notes=item.notes,
            extras=extras,
        )

    def _to_detail(self, order: Order, *, include_internal: bool = False) -> OrderDetailResponse:
        items = [self._to_item_response(item) for item in order.items if item.deleted_at is None]
        timeline = [
            OrderTimelineEventResponse.model_validate(event)
            for event in order.timeline
            if event.deleted_at is None
        ]
        return OrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            status=order.status,
            payment_status=order.payment_status,
            payment_method=order.payment_method,
            currency=order.currency,
            subtotal=order.subtotal,
            discount=order.discount,
            tax=order.tax,
            delivery_fee=order.delivery_fee,
            grand_total=order.grand_total,
            coupon_code=order.coupon_code,
            notes=order.notes,
            kitchen_notes=order.kitchen_notes if include_internal else None,
            internal_notes=order.internal_notes if include_internal else None,
            delivery_address_snapshot=order.delivery_address_snapshot,
            estimated_preparation_minutes=order.estimated_preparation_minutes,
            estimated_delivery_time=order.estimated_delivery_time,
            items=items,
            timeline=timeline,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def _to_list_item(self, order: Order) -> OrderListItemResponse:
        item_count = sum(i.quantity for i in order.items if i.deleted_at is None) if order.items else 0
        return OrderListItemResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            payment_method=order.payment_method,
            grand_total=order.grand_total,
            currency=order.currency,
            item_count=item_count,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def _resolve_address(self, user: User, address_id: UUID | None) -> Address:
        if address_id is not None:
            address = await self._addresses.get_for_user(address_id, user.id)
            if address is None:
                raise NotFoundException("Address not found")
            return address
        addresses = await self._addresses.list_for_user(user.id)
        default = next((a for a in addresses if a.is_default), None)
        if default is None:
            raise ValidationException("Default delivery address is required")
        return default

    async def place_order(self, user: User, payload: PlaceOrderRequest) -> OrderDetailResponse:
        if payload.idempotency_key:
            existing_id = await self._cache.get_idempotent_order_id(user.id, payload.idempotency_key)
            if existing_id is not None:
                detail = await self._orders.get_for_user(existing_id, user.id)
                if detail is not None:
                    return self._to_detail(detail, include_internal=False)

        if not await self._cache.acquire_checkout_lock(user.id):
            raise ConflictException("Checkout already in progress. Please wait.")

        try:
            if payload.payment_method == PaymentMethod.ONLINE:
                raise ValidationException("Online payment is not available yet")
            if payload.payment_method != PaymentMethod.CASH_ON_DELIVERY:
                raise ValidationException("Unsupported payment method")

            # Lock cart first so pricing + conversion stay in one transaction.
            locked = await self._carts.get_active_for_update(user.id)
            if locked is None or locked.status == CartStatus.CONVERTED:
                raise ValidationException("Cart is empty or already checked out")

            validation = await self._checkout.validate(user, commit=False)
            if not validation.is_valid:
                logger.warning(
                    "Failed checkout | user_id={} | issues={}",
                    user.id,
                    [i.code for i in validation.issues],
                )
                raise ValidationException(
                    "Checkout validation failed",
                    details=[i.model_dump() for i in validation.issues],
                )

            cart = await self._carts.get_active_for_user(user.id)
            if cart is None or cart.status == CartStatus.CONVERTED:
                raise ValidationException("Cart is empty or already checked out")

            await self._cart_service.recalculate(cart)
            active_items = [item for item in cart.items if item.deleted_at is None]
            if not active_items:
                raise ValidationException("Cart is empty")

            address = await self._resolve_address(user, payload.address_id)
            summary = self._summary.build(cart)
            order_number = await self._next_order_number()
            now = datetime.now(UTC)
            eta = now + timedelta(minutes=self._settings.estimated_delivery_minutes)

            order = Order(
                order_number=order_number,
                user_id=user.id,
                address_id=address.id,
                delivery_address_snapshot=self._address_snapshot(address),
                status=OrderStatus.PENDING,
                currency=cart.currency,
                subtotal=cart.subtotal,
                tax=cart.tax,
                delivery_fee=cart.delivery_fee,
                discount=cart.discount,
                grand_total=cart.grand_total,
                payment_method=payload.payment_method,
                payment_status=PaymentStatus.PENDING,
                notes=payload.notes or cart.notes,
                estimated_preparation_minutes=summary.estimated_preparation_time_minutes,
                estimated_delivery_time=eta,
                coupon_id=cart.coupon_id,
                coupon_code=cart.coupon.code if cart.coupon else None,
                created_by=user.id,
            )
            await self._orders.add(order)
            await self._session.flush()

            for cart_item in active_items:
                product = cart_item.product
                variant = cart_item.variant
                prep = None
                if variant and variant.preparation_time_minutes is not None:
                    prep = variant.preparation_time_minutes
                elif product and product.preparation_time_minutes is not None:
                    prep = product.preparation_time_minutes

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    variant_id=cart_item.variant_id,
                    product_name=product.name if product else "Product",
                    product_slug=product.slug if product else None,
                    variant_name=variant.name if variant else None,
                    variant_size=variant.size.value if variant and variant.size else None,
                    image_url=product.image_url if product else None,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    discount_price=cart_item.discount_price,
                    subtotal=cart_item.subtotal,
                    preparation_time_minutes=prep,
                    extras_snapshot=cart_item.extras_snapshot,
                    product_snapshot={
                        "product_id": str(cart_item.product_id),
                        "name": product.name if product else None,
                        "slug": product.slug if product else None,
                        "image_url": product.image_url if product else None,
                        "base_price": str(product.base_price) if product else None,
                    },
                    notes=cart_item.special_instructions,
                )
                self._session.add(order_item)
                await self._session.flush()

                for extra in cart_item.extras:
                    if extra.deleted_at is not None:
                        continue
                    option = extra.option
                    self._session.add(
                        OrderItemExtra(
                            order_item_id=order_item.id,
                            option_id=extra.option_id,
                            option_name=option.name if option else "Extra",
                            option_type=(
                                option.option_type.value if option and option.option_type else None
                            ),
                            quantity=extra.quantity,
                            unit_price=extra.unit_price,
                        )
                    )

            if cart.coupon_id is not None:
                coupon = await self._coupon_rows.get_for_update(cart.coupon_id)
                if coupon is None:
                    raise ValidationException("Coupon is no longer available")
                await self._coupons.validate_for_user(
                    code=coupon.code,
                    user_id=user.id,
                    subtotal=cart.subtotal,
                )
                coupon.used_count = int(coupon.used_count or 0) + 1
                order.coupon_id = coupon.id
                order.coupon_code = coupon.code
                await self._coupon_usages.add(
                    CouponUsage(
                        user_id=user.id,
                        coupon_id=coupon.id,
                        order_id=order.id,
                        discount_applied=cart.discount,
                    )
                )

            await self._add_timeline(
                order,
                status=OrderStatus.PENDING,
                performed_by=user.id,
                notes="Order placed successfully",
            )
            await self._cart_service.convert_cart_after_order(cart)

            await self._session.commit()
            await self._cache.invalidate_order(user_id=user.id, order_id=order.id)
            await self._cart_cache.invalidate_user(user.id)
            await self._invalidate_dashboard()
            if payload.idempotency_key:
                await self._cache.store_idempotent_order_id(
                    user.id, payload.idempotency_key, order.id
                )

            detail = await self._orders.get_detail(order.id)
            assert detail is not None
            logger.info(
                "Order created | order_id={} | order_number={} | user_id={}",
                order.id,
                order.order_number,
                user.id,
            )
            # Email only after a successful commit — failures must never undo the order.
            if self._email is not None:
                try:
                    email_payload = build_order_email_payload(
                        detail,
                        user,
                        brand_name=self._settings.email_brand_name,
                        logo_url=self._settings.email_logo_url or None,
                    )
                    self._email.notify_owner_new_order(email_payload)
                except Exception:
                    logger.exception(
                        "Email queued failed | order_id={} | post_commit_hook",
                        order.id,
                    )
            return self._to_detail(detail, include_internal=False)

        except Exception:
            await self._session.rollback()
            logger.exception("Rollback events | checkout failed | user_id={}", user.id)
            raise
        finally:
            await self._cache.release_checkout_lock(user.id)

    async def list_my_orders(
        self,
        user: User,
        filters: OrderFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[OrderListItemResponse], PaginationMeta]:
        rows, total = await self._orders.list_for_user(
            user.id,
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [self._to_list_item(row) for row in rows], meta

    async def get_my_order(self, user: User, order_id: UUID) -> OrderDetailResponse:
        order = await self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise NotFoundException("Order not found")
        self._ownership.ensure_owner_or_self(user, order.user_id, resource_name="order")
        return self._to_detail(order, include_internal=False)

    async def track_my_order(self, user: User, order_id: UUID) -> OrderTrackingResponse:
        cached = await self._cache.get_json(self._cache.tracking_key(order_id))
        if cached is not None and str(cached.get("user_id")) == str(user.id):
            return OrderTrackingResponse.model_validate(
                {k: v for k, v in cached.items() if k != "user_id"}
            )

        order = await self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise NotFoundException("Order not found")
        tracking = OrderTrackingResponse(
            order_id=order.id,
            order_number=order.order_number,
            current_status=order.status,
            payment_status=order.payment_status,
            timeline=[
                OrderTimelineEventResponse.model_validate(event)
                for event in order.timeline
                if event.deleted_at is None
            ],
            estimated_preparation_minutes=order.estimated_preparation_minutes,
            estimated_delivery_time=order.estimated_delivery_time,
            last_updated=order.updated_at,
        )
        payload = tracking.model_dump(mode="json")
        payload["user_id"] = str(order.user_id)
        await self._cache.set_json(self._cache.tracking_key(order_id), payload)
        logger.info("Tracking viewed | order_id={} | user_id={}", order_id, user.id)
        return tracking

    async def cancel_my_order(
        self,
        user: User,
        order_id: UUID,
        payload: CancelOrderRequest,
    ) -> OrderDetailResponse:
        order = await self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise NotFoundException("Order not found")
        if order.status not in CUSTOMER_CANCELABLE:
            raise ValidationException("Order can no longer be cancelled")
        window = timedelta(minutes=self._settings.order_cancel_window_minutes)
        if datetime.now(UTC) - order.created_at > window:
            raise ValidationException("Cancellation window has expired")

        order.status = OrderStatus.CANCELLED
        if order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.CANCELLED
        await self._add_timeline(
            order,
            status=OrderStatus.CANCELLED,
            performed_by=user.id,
            notes=payload.reason or "Cancelled by customer",
        )
        await self._session.commit()
        await self._cache.invalidate_order(user_id=user.id, order_id=order.id)
        await self._invalidate_dashboard()
        logger.info("Order cancelled | order_id={} | user_id={}", order_id, user.id)
        detail = await self._orders.get_detail(order_id)
        assert detail is not None
        return self._to_detail(detail, include_internal=False)

    async def list_admin_orders(
        self,
        filters: OrderFilterParams,
        pagination: PaginationParams,
    ) -> tuple[list[OrderListItemResponse], PaginationMeta]:
        rows, total = await self._orders.list_all_filtered(
            filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        meta = PaginationMeta.from_totals(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
        )
        return [self._to_list_item(row) for row in rows], meta

    async def get_admin_order(self, order_id: UUID) -> OrderDetailResponse:
        order = await self._orders.get_detail(order_id)
        if order is None:
            raise NotFoundException("Order not found")
        return self._to_detail(order, include_internal=True)

    async def update_status(
        self,
        actor: User,
        order_id: UUID,
        payload: UpdateOrderStatusRequest,
    ) -> OrderDetailResponse:
        order = await self._orders.get_detail(order_id)
        if order is None:
            raise NotFoundException("Order not found")
        allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, set())
        if payload.status == order.status:
            raise ValidationException("Order is already in this status")
        if payload.status not in allowed:
            raise ValidationException(
                f"Cannot transition from {order.status.value} to {payload.status.value}",
            )
        order.status = payload.status
        if payload.status == OrderStatus.CANCELLED and order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.CANCELLED
        if payload.status == OrderStatus.REFUNDED:
            order.payment_status = PaymentStatus.REFUNDED
        await self._add_timeline(
            order,
            status=payload.status,
            performed_by=actor.id,
            notes=payload.notes,
        )
        await self._session.commit()
        await self._cache.invalidate_order(user_id=order.user_id, order_id=order.id)
        await self._invalidate_dashboard()
        logger.info("Status changed | order_id={} | status={}", order_id, payload.status.value)
        detail = await self._orders.get_detail(order_id)
        assert detail is not None
        return self._to_detail(detail, include_internal=True)

    async def update_payment(
        self,
        actor: User,
        order_id: UUID,
        payload: UpdatePaymentStatusRequest,
    ) -> OrderDetailResponse:
        order = await self._orders.get_detail(order_id)
        if order is None:
            raise NotFoundException("Order not found")
        order.payment_status = payload.payment_status
        await self._add_timeline(
            order,
            status=order.status,
            performed_by=actor.id,
            notes=payload.notes or f"Payment status: {payload.payment_status.value}",
        )
        await self._session.commit()
        await self._cache.invalidate_order(user_id=order.user_id, order_id=order.id)
        await self._invalidate_dashboard()
        logger.info(
            "Payment updated | order_id={} | payment_status={}",
            order_id,
            payload.payment_status.value,
        )
        detail = await self._orders.get_detail(order_id)
        assert detail is not None
        return self._to_detail(detail, include_internal=True)

    async def update_notes(
        self,
        actor: User,
        order_id: UUID,
        payload: UpdateOrderNotesRequest,
    ) -> OrderDetailResponse:
        order = await self._orders.get_detail(order_id)
        if order is None:
            raise NotFoundException("Order not found")
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No note fields provided")
        for key, value in data.items():
            setattr(order, key, value)
        await self._session.commit()
        await self._cache.invalidate_order(user_id=order.user_id, order_id=order.id)
        logger.info("Order updated | order_id={} | by={}", order_id, actor.id)
        detail = await self._orders.get_detail(order_id)
        assert detail is not None
        return self._to_detail(detail, include_internal=True)
