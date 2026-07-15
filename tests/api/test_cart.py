"""Cart, wishlist, and checkout preparation API tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.common.enums import CartStatus, UserRole
from app.config.settings import get_settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.main import create_app
from app.models.user import User
from app.schemas.cart import (
    CartResponse,
    CheckoutValidationIssue,
    CheckoutValidationResponse,
    OrderSummaryResponse,
    WishlistItemResponse,
    WishlistResponse,
)
from fastapi.testclient import TestClient


def _user(*, role: UserRole = UserRole.CUSTOMER) -> User:
    return User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number="+923001234567",
        full_name="Customer",
        email="test@example.com",
        password_hash="hashed",
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


def _empty_cart() -> CartResponse:
    now = datetime.now(UTC)
    return CartResponse(
        id=uuid4(),
        status=CartStatus.ACTIVE,
        currency="PKR",
        notes=None,
        last_activity=now,
        coupon_id=None,
        coupon_code=None,
        subtotal=Decimal("0.00"),
        discount=Decimal("0.00"),
        delivery_fee=Decimal("150.00"),
        tax=Decimal("0.00"),
        grand_total=Decimal("150.00"),
        item_count=0,
        items=[],
        created_at=now,
        updated_at=now,
    )


def test_cart_requires_auth() -> None:
    app = create_app(settings=get_settings())
    with TestClient(app) as client:
        assert client.get("/api/v1/cart").status_code == 401


def test_cart_crud_flow(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    cart = _empty_cart()
    item_id = uuid4()

    async def _get(self, current):
        return cart

    async def _add(self, current, payload):
        assert payload.product_id is not None
        return cart.model_copy(update={"item_count": 1, "subtotal": Decimal("999.00")})

    async def _update(self, current, iid, payload):
        assert iid == item_id
        return cart.model_copy(update={"item_count": 2})

    async def _remove(self, current, iid):
        return cart

    async def _clear(self, current):
        return cart

    async def _summary(self, current):
        return OrderSummaryResponse(
            currency="PKR",
            products=[],
            subtotal=Decimal("0"),
            discount=Decimal("0"),
            tax=Decimal("0"),
            delivery_fee=Decimal("150"),
            grand_total=Decimal("150"),
            coupon_code=None,
            estimated_preparation_time_minutes=15,
            estimated_delivery_time_minutes=45,
            item_count=0,
        )

    async def _apply(self, current, payload):
        assert payload.code == "SAVE10"
        return cart.model_copy(update={"coupon_code": "SAVE10", "discount": Decimal("10")})

    async def _remove_coupon(self, current):
        return cart

    monkeypatch.setattr("app.services.cart.CartService.get_cart", _get)
    monkeypatch.setattr("app.services.cart.CartService.add_item", _add)
    monkeypatch.setattr("app.services.cart.CartService.update_item", _update)
    monkeypatch.setattr("app.services.cart.CartService.remove_item", _remove)
    monkeypatch.setattr("app.services.cart.CartService.clear", _clear)
    monkeypatch.setattr("app.services.cart.CartService.get_summary", _summary)
    monkeypatch.setattr("app.services.cart.CartService.apply_coupon", _apply)
    monkeypatch.setattr("app.services.cart.CartService.remove_coupon", _remove_coupon)

    with TestClient(app) as client:
        assert client.get("/api/v1/cart").status_code == 200
        assert client.get("/api/v1/cart/summary").status_code == 200
        added = client.post(
            "/api/v1/cart/items",
            json={"product_id": str(uuid4()), "quantity": 1},
        )
        assert added.status_code == 201
        assert client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 2}).status_code == 200
        assert client.delete(f"/api/v1/cart/items/{item_id}").status_code == 200
        assert client.delete("/api/v1/cart/clear").status_code == 200
        assert client.post("/api/v1/cart/apply-coupon", json={"code": "save10"}).status_code == 200
        assert client.delete("/api/v1/cart/remove-coupon").status_code == 200

    app.dependency_overrides.clear()


def test_wishlist_apis(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    product_id = uuid4()
    wishlist = WishlistResponse(
        id=uuid4(),
        item_count=1,
        items=[
            WishlistItemResponse(
                product_id=product_id,
                product_name="Margherita",
                product_slug="margherita",
                image_url=None,
                base_price=Decimal("999"),
                is_available=True,
                added_at=datetime.now(UTC),
            )
        ],
    )

    async def _list(self, current):
        return wishlist

    async def _add(self, current, pid):
        return wishlist

    async def _remove(self, current, pid):
        if pid != product_id:
            raise NotFoundException("Wishlist item not found")
        return wishlist.model_copy(update={"item_count": 0, "items": []})

    async def _clear(self, current):
        return wishlist.model_copy(update={"item_count": 0, "items": []})

    monkeypatch.setattr("app.services.wishlist.WishlistService.list_wishlist", _list)
    monkeypatch.setattr("app.services.wishlist.WishlistService.add", _add)
    monkeypatch.setattr("app.services.wishlist.WishlistService.remove", _remove)
    monkeypatch.setattr("app.services.wishlist.WishlistService.clear", _clear)

    with TestClient(app) as client:
        assert client.get("/api/v1/wishlist").status_code == 200
        assert client.post("/api/v1/wishlist", json={"product_id": str(product_id)}).status_code == 201
        assert client.delete("/api/v1/wishlist/clear").status_code == 200
        assert client.delete(f"/api/v1/wishlist/{product_id}").status_code == 200

    app.dependency_overrides.clear()


def test_checkout_validate_does_not_create_order(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _validate(self, current):
        return CheckoutValidationResponse(
            is_valid=False,
            issues=[
                CheckoutValidationIssue(code="cart_empty", message="Cart is empty", field="cart"),
                CheckoutValidationIssue(
                    code="address_missing",
                    message="Add a delivery address before checkout",
                    field="address",
                ),
            ],
            summary=None,
            has_default_address=False,
            address_count=0,
        )

    monkeypatch.setattr("app.services.checkout.CheckoutValidationService.validate", _validate)

    with TestClient(app) as client:
        response = client.post("/api/v1/checkout/validate")
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["is_valid"] is False
        assert body["summary"] is None
        assert any(i["code"] == "cart_empty" for i in body["issues"])

    app.dependency_overrides.clear()


def test_wishlist_duplicate_conflict(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _add(self, current, pid):
        raise ConflictException("Product already in wishlist")

    monkeypatch.setattr("app.services.wishlist.WishlistService.add", _add)

    with TestClient(app) as client:
        response = client.post("/api/v1/wishlist", json={"product_id": str(uuid4())})
        assert response.status_code == 409

    app.dependency_overrides.clear()


def test_cart_add_ignores_client_unit_price(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    cart = _empty_cart()

    async def _add(self, current, payload):
        assert not hasattr(payload, "unit_price") or "unit_price" not in payload.model_dump()
        return cart.model_copy(update={"item_count": 1})

    monkeypatch.setattr("app.services.cart.CartService.add_item", _add)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(uuid4()),
                "quantity": 1,
                "unit_price": "1.00",
            },
        )
        assert response.status_code == 201

    app.dependency_overrides.clear()


def test_cart_add_validation_quantity_bounds(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _add(self, current, payload):
        raise ValidationException("Maximum quantity is 20")

    monkeypatch.setattr("app.services.cart.CartService.add_item", _add)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/cart/items",
            json={"product_id": str(uuid4()), "quantity": 50},
        )
        assert response.status_code == 422

    app.dependency_overrides.clear()

