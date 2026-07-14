"""Order management API tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.common.enums import OrderStatus, PaymentMethod, PaymentStatus, UserRole
from app.config.settings import get_settings
from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.main import create_app
from app.models.user import User
from app.schemas.orders import (
    OrderDetailResponse,
    OrderListItemResponse,
    OrderTrackingResponse,
    OrderTimelineEventResponse,
)
from app.schemas.pagination import PaginationMeta
from fastapi.testclient import TestClient


def _user(*, role: UserRole = UserRole.CUSTOMER) -> User:
    return User(
        id=uuid4(),
        phone_number="+923001234567",
        full_name="Customer",
        role=role,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )


def _override_auth(app, user: User) -> None:
    from app.dependencies import auth as auth_deps

    async def _current() -> User:
        return user

    app.dependency_overrides[auth_deps.get_current_user] = _current
    app.dependency_overrides[auth_deps.get_verified_user] = _current


def _order_detail(*, user_id=None) -> OrderDetailResponse:
    now = datetime.now(UTC)
    oid = uuid4()
    return OrderDetailResponse(
        id=oid,
        order_number="PP-2026-000001",
        user_id=user_id or uuid4(),
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        payment_method=PaymentMethod.CASH_ON_DELIVERY,
        currency="PKR",
        subtotal=Decimal("999.00"),
        discount=Decimal("0"),
        tax=Decimal("0"),
        delivery_fee=Decimal("150"),
        grand_total=Decimal("1149.00"),
        coupon_code=None,
        notes=None,
        kitchen_notes=None,
        internal_notes=None,
        delivery_address_snapshot={"city": "Lahore"},
        estimated_preparation_minutes=30,
        estimated_delivery_time=now,
        items=[],
        timeline=[
            OrderTimelineEventResponse(
                id=uuid4(),
                status=OrderStatus.PENDING,
                title="Order Created",
                notes=None,
                performed_by=None,
                created_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )


def test_place_order_requires_auth() -> None:
    app = create_app(settings=get_settings())
    with TestClient(app) as client:
        assert client.post("/api/v1/orders", json={}).status_code == 401


def test_customer_order_flow(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    detail = _order_detail(user_id=user.id)
    meta = PaginationMeta.from_totals(page=1, page_size=20, total_items=1)

    async def _place(self, current, payload):
        assert payload.payment_method == PaymentMethod.CASH_ON_DELIVERY
        return detail

    async def _list(self, current, filters, pagination):
        return [
            OrderListItemResponse(
                id=detail.id,
                order_number=detail.order_number,
                status=detail.status,
                payment_status=detail.payment_status,
                payment_method=detail.payment_method,
                grand_total=detail.grand_total,
                currency=detail.currency,
                item_count=1,
                created_at=detail.created_at,
                updated_at=detail.updated_at,
            )
        ], meta

    async def _get(self, current, order_id):
        if order_id != detail.id:
            raise NotFoundException("Order not found")
        return detail

    async def _track(self, current, order_id):
        return OrderTrackingResponse(
            order_id=detail.id,
            order_number=detail.order_number,
            current_status=detail.status,
            payment_status=detail.payment_status,
            timeline=detail.timeline,
            estimated_preparation_minutes=detail.estimated_preparation_minutes,
            estimated_delivery_time=detail.estimated_delivery_time,
            last_updated=detail.updated_at,
        )

    async def _cancel(self, current, order_id, payload):
        return detail.model_copy(update={"status": OrderStatus.CANCELLED})

    monkeypatch.setattr("app.services.order.OrderService.place_order", _place)
    monkeypatch.setattr("app.services.order.OrderService.list_my_orders", _list)
    monkeypatch.setattr("app.services.order.OrderService.get_my_order", _get)
    monkeypatch.setattr("app.services.order.OrderService.track_my_order", _track)
    monkeypatch.setattr("app.services.order.OrderService.cancel_my_order", _cancel)

    with TestClient(app) as client:
        placed = client.post("/api/v1/orders", json={"payment_method": "cash_on_delivery"})
        assert placed.status_code == 201
        assert placed.json()["data"]["order_number"] == "PP-2026-000001"

        listing = client.get("/api/v1/orders")
        assert listing.status_code == 200
        assert listing.json()["meta"]["total_items"] == 1

        assert client.get(f"/api/v1/orders/{detail.id}").status_code == 200
        assert client.get(f"/api/v1/orders/{detail.id}/tracking").status_code == 200
        cancelled = client.patch(f"/api/v1/orders/{detail.id}/cancel", json={"reason": "changed mind"})
        assert cancelled.status_code == 200
        assert cancelled.json()["data"]["status"] == "cancelled"

    app.dependency_overrides.clear()


def test_customer_cannot_access_foreign_order(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _get(self, current, order_id):
        raise NotFoundException("Order not found")

    monkeypatch.setattr("app.services.order.OrderService.get_my_order", _get)

    with TestClient(app) as client:
        assert client.get(f"/api/v1/orders/{uuid4()}").status_code == 404

    app.dependency_overrides.clear()


def test_owner_order_apis(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    owner = _user(role=UserRole.OWNER)
    _override_auth(app, owner)
    detail = _order_detail()
    meta = PaginationMeta.from_totals(page=1, page_size=20, total_items=1)

    async def _list(self, filters, pagination):
        return [
            OrderListItemResponse(
                id=detail.id,
                order_number=detail.order_number,
                status=detail.status,
                payment_status=detail.payment_status,
                payment_method=detail.payment_method,
                grand_total=detail.grand_total,
                currency=detail.currency,
                item_count=1,
                created_at=detail.created_at,
                updated_at=detail.updated_at,
            )
        ], meta

    async def _get(self, order_id):
        return detail.model_copy(update={"internal_notes": "kitchen rush"})

    async def _status(self, actor, order_id, payload):
        return detail.model_copy(update={"status": payload.status})

    async def _payment(self, actor, order_id, payload):
        return detail.model_copy(update={"payment_status": payload.payment_status})

    async def _notes(self, actor, order_id, payload):
        return detail.model_copy(update={"internal_notes": payload.internal_notes})

    monkeypatch.setattr("app.services.order.OrderService.list_admin_orders", _list)
    monkeypatch.setattr("app.services.order.OrderService.get_admin_order", _get)
    monkeypatch.setattr("app.services.order.OrderService.update_status", _status)
    monkeypatch.setattr("app.services.order.OrderService.update_payment", _payment)
    monkeypatch.setattr("app.services.order.OrderService.update_notes", _notes)

    with TestClient(app) as client:
        assert client.get("/api/v1/admin/orders").status_code == 200
        assert client.get(f"/api/v1/admin/orders/{detail.id}").status_code == 200
        status_resp = client.patch(
            f"/api/v1/admin/orders/{detail.id}/status",
            json={"status": "preparing"},
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["data"]["status"] == "preparing"
        pay = client.patch(
            f"/api/v1/admin/orders/{detail.id}/payment",
            json={"payment_status": "paid"},
        )
        assert pay.status_code == 200
        notes = client.patch(
            f"/api/v1/admin/orders/{detail.id}/notes",
            json={"internal_notes": "VIP"},
        )
        assert notes.status_code == 200

    app.dependency_overrides.clear()


def test_customer_forbidden_from_admin_orders() -> None:
    app = create_app(settings=get_settings())
    customer = _user(role=UserRole.CUSTOMER)
    _override_auth(app, customer)
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/orders").status_code == 403
    app.dependency_overrides.clear()


def test_checkout_validation_failure_surface(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _place(self, current, payload):
        raise ValidationException(
            "Checkout validation failed",
            details=[{"code": "cart_empty", "message": "Cart is empty"}],
        )

    monkeypatch.setattr("app.services.order.OrderService.place_order", _place)

    with TestClient(app) as client:
        response = client.post("/api/v1/orders", json={})
        assert response.status_code == 422

    app.dependency_overrides.clear()
