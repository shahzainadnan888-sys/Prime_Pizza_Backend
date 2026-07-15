"""Kitchen dashboard orchestration for chef order boards."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import OrderStatus
from app.core.exceptions import NotFoundException, ValidationException
from app.models.order import Order
from app.models.user import User
from app.repositories.order import OrderRepository
from app.schemas.kitchen import (
    KitchenActionRequest,
    KitchenBoardResponse,
    KitchenOrderCardResponse,
    KitchenOrderItemResponse,
    KitchenStatusUpdateRequest,
)
from app.schemas.orders import UpdateOrderStatusRequest
from app.services.base import BaseService
from app.services.order import OrderService

# Board groupings for the kitchen UI
_INCOMING = {OrderStatus.PENDING, OrderStatus.CONFIRMED}
_PREPARING = {OrderStatus.PREPARING}
_READY = {OrderStatus.READY, OrderStatus.OUT_FOR_DELIVERY}
_COMPLETED = {OrderStatus.DELIVERED}
_CANCELLED = {OrderStatus.CANCELLED, OrderStatus.REFUNDED}

_ACTION_TARGET: dict[str, OrderStatus] = {
    "accept": OrderStatus.CONFIRMED,
    "start-preparing": OrderStatus.PREPARING,
    "mark-ready": OrderStatus.READY,
    "complete": OrderStatus.DELIVERED,
    "cancel": OrderStatus.CANCELLED,
}

_STATUS_TARGET: dict[str, OrderStatus] = {
    "pending": OrderStatus.PENDING,
    "preparing": OrderStatus.PREPARING,
    "ready": OrderStatus.READY,
    "completed": OrderStatus.DELIVERED,
    "cancelled": OrderStatus.CANCELLED,
}


class KitchenService(BaseService):
    service_name = "kitchen"

    def __init__(self, *, session: AsyncSession, order_service: OrderService) -> None:
        self._session = session
        self._orders = OrderRepository(session)
        self._order_service = order_service

    def _delivery_type(self, order: Order) -> str:
        snapshot = order.delivery_address_snapshot or {}
        raw = str(snapshot.get("delivery_type") or snapshot.get("fulfillment_type") or "").strip().lower()
        if raw in {"pickup", "takeaway", "collection"}:
            return "pickup"
        if raw in {"delivery", "deliver"}:
            return "delivery"
        # Infer: address present ⇒ delivery, otherwise pickup
        has_address = any(
            snapshot.get(key)
            for key in ("street", "area", "city", "address_line1", "recipient_name")
        )
        return "delivery" if has_address else "pickup"

    def _to_card(self, order: Order) -> KitchenOrderCardResponse:
        snapshot = order.delivery_address_snapshot or {}
        customer = order.user
        customer_name = (
            str(snapshot.get("recipient_name") or "").strip()
            or (customer.full_name if customer else None)
            or "Customer"
        )
        customer_phone = (
            str(snapshot.get("phone_number") or "").strip()
            or (customer.phone_number if customer else None)
        )
        notes = order.notes or order.kitchen_notes
        items = [
            KitchenOrderItemResponse(
                product_name=item.product_name,
                variant_name=item.variant_name,
                quantity=item.quantity,
                special_instructions=item.notes,
            )
            for item in order.items
            if item.deleted_at is None
        ]
        return KitchenOrderCardResponse(
            id=order.id,
            order_number=order.order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            items=items,
            special_instructions=notes,
            notes=notes,
            payment_status=order.payment_status,
            payment_method=(
                order.payment_method.value.replace("_", " ").title()
                if order.payment_method
                else None
            ),
            delivery_type=self._delivery_type(order),
            order_time=order.created_at,
            status=order.status,
            estimated_time=order.estimated_delivery_time,
            estimated_preparation_minutes=order.estimated_preparation_minutes,
            latitude=float(order.latitude) if order.latitude is not None else None,
            longitude=float(order.longitude) if order.longitude is not None else None,
            gps_accuracy=float(order.gps_accuracy) if order.gps_accuracy is not None else None,
        )

    async def get_board(self) -> KitchenBoardResponse:
        rows = await self._orders.list_by_statuses(
            list(_INCOMING | _PREPARING | _READY | _COMPLETED | _CANCELLED),
            limit=200,
        )
        board = KitchenBoardResponse()
        for order in rows:
            card = self._to_card(order)
            if order.status in _INCOMING:
                board.incoming.append(card)
            elif order.status in _PREPARING:
                board.preparing.append(card)
            elif order.status in _READY:
                board.ready.append(card)
            elif order.status in _COMPLETED:
                board.completed.append(card)
            elif order.status in _CANCELLED:
                board.cancelled.append(card)
        return board

    async def list_status(self, status_group: str) -> list[KitchenOrderCardResponse]:
        mapping: dict[str, set[OrderStatus]] = {
            "incoming": _INCOMING,
            "pending": _INCOMING,
            "preparing": _PREPARING,
            "ready": _READY,
            "completed": _COMPLETED,
            "cancelled": _CANCELLED,
        }
        statuses = mapping.get(status_group)
        if statuses is None:
            raise ValidationException(f"Unknown kitchen board: {status_group}")
        rows = await self._orders.list_by_statuses(list(statuses), limit=100)
        return [self._to_card(order) for order in rows]

    async def get_order(self, order_id: UUID) -> KitchenOrderCardResponse:
        order = await self._orders.get_detail(order_id)
        if order is None:
            raise NotFoundException("Order not found")
        return self._to_card(order)

    async def apply_action(
        self,
        chef: User,
        order_id: UUID,
        action: str,
        payload: KitchenActionRequest | None = None,
    ) -> KitchenOrderCardResponse:
        target = _ACTION_TARGET.get(action)
        if target is None:
            raise ValidationException(f"Unknown kitchen action: {action}")

        notes = payload.notes if payload else None
        await self._order_service.update_status(
            chef,
            order_id,
            UpdateOrderStatusRequest(status=target, notes=notes),
        )
        order = await self._orders.get_detail(order_id)
        assert order is not None
        return self._to_card(order)

    async def update_status(
        self,
        chef: User,
        order_id: UUID,
        payload: KitchenStatusUpdateRequest,
    ) -> KitchenOrderCardResponse:
        target = _STATUS_TARGET.get(payload.status)
        if target is None:
            raise ValidationException(f"Unsupported kitchen status: {payload.status}")
        await self._order_service.update_status(
            chef,
            order_id,
            UpdateOrderStatusRequest(status=target, notes=payload.notes),
        )
        order = await self._orders.get_detail(order_id)
        assert order is not None
        return self._to_card(order)
