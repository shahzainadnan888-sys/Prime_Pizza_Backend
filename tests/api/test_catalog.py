"""Catalog / product module API tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from app.common.enums import DealType, StockStatus, UserRole
from app.config.settings import get_settings
from app.core.exceptions import NotFoundException
from app.main import create_app
from app.models.user import User
from app.schemas.catalog import (
    CategoryResponse,
    DealResponse,
    ProductDetailResponse,
    ProductImageResponse,
    ProductListItemResponse,
)
from app.schemas.pagination import PaginationMeta
from fastapi.testclient import TestClient


def _user(*, role: UserRole) -> User:
    return User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number="+923001234567",
        full_name="Test User",
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


def _category() -> CategoryResponse:
    now = datetime.now(UTC)
    return CategoryResponse(
        id=uuid4(),
        name="Pizza",
        slug="pizza",
        description="Hot pizzas",
        image_url=None,
        display_order=1,
        is_visible=True,
        seo_title="Pizza",
        seo_description=None,
        seo_keywords=None,
        created_at=now,
        updated_at=now,
    )


def _product_list_item() -> ProductListItemResponse:
    return ProductListItemResponse(
        id=uuid4(),
        category_id=uuid4(),
        name="Margherita",
        slug="margherita",
        short_description="Classic",
        base_price=Decimal("999.00"),
        discount_price=Decimal("899.00"),
        image_url=None,
        is_available=True,
        stock_status=StockStatus.IN_STOCK,
        preparation_time_minutes=20,
        calories=250,
        is_featured=True,
        is_popular=True,
        is_best_seller=False,
        tags=["vegetarian"],
        sort_order=1,
        created_at=datetime.now(UTC),
    )


def test_list_categories(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    cat = _category()

    async def _list(self):
        return [cat]

    monkeypatch.setattr("app.services.category.CategoryService.list_public", _list)
    with TestClient(app) as client:
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        assert response.json()["data"][0]["slug"] == "pizza"


def test_get_category_and_product(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    cat = _category()
    item = _product_list_item()
    detail = ProductDetailResponse(
        **item.model_dump(),
        description="Fresh mozzarella",
        is_visible=True,
        seo_title=None,
        seo_description=None,
        seo_keywords=None,
        updated_at=datetime.now(UTC),
        images=[],
        variants=[],
        extras=[],
        category=cat,
    )

    async def _cat(self, slug: str):
        if slug != "pizza":
            raise NotFoundException("Category not found")
        return cat

    async def _product(self, slug: str):
        if slug != "margherita":
            raise NotFoundException("Product not found")
        return detail

    monkeypatch.setattr("app.services.category.CategoryService.get_by_slug", _cat)
    monkeypatch.setattr("app.services.product.ProductService.get_by_slug", _product)

    with TestClient(app) as client:
        assert client.get("/api/v1/categories/pizza").status_code == 200
        assert client.get("/api/v1/products/margherita").json()["data"]["name"] == "Margherita"
        assert client.get("/api/v1/products/missing").status_code == 404


def test_product_list_search_featured_popular(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    item = _product_list_item()
    meta = PaginationMeta.from_totals(page=1, page_size=20, total_items=1)

    async def _filter(self, filters, pagination):
        return [item], meta

    async def _search(self, query, pagination):
        assert query == "marg"
        return [item], meta

    async def _featured(self):
        return [item]

    async def _popular(self):
        return [item]

    async def _recommended(self, *, product_slug=None, category=None):
        return [item]

    monkeypatch.setattr("app.services.search.ProductFilterService.filter", _filter)
    monkeypatch.setattr("app.services.search.ProductSearchService.search", _search)
    monkeypatch.setattr("app.services.product.ProductService.list_featured", _featured)
    monkeypatch.setattr("app.services.product.ProductService.list_popular", _popular)
    monkeypatch.setattr("app.services.product.ProductService.list_recommended", _recommended)

    with TestClient(app) as client:
        listing = client.get("/api/v1/products", params={"is_featured": True, "sort": "price_asc"})
        assert listing.status_code == 200
        assert listing.json()["meta"]["total_items"] == 1

        search = client.get("/api/v1/products/search", params={"q": "marg"})
        assert search.status_code == 200
        assert search.json()["data"][0]["slug"] == "margherita"

        assert client.get("/api/v1/products/featured").status_code == 200
        assert client.get("/api/v1/products/popular").status_code == 200
        assert client.get("/api/v1/products/recommended").status_code == 200


def test_deals_public(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    now = datetime.now(UTC)
    deal = DealResponse(
        id=uuid4(),
        name="Family Feast",
        slug="family-feast",
        description="Share meal",
        deal_type=DealType.FAMILY,
        deal_price=Decimal("2499.00"),
        discount_percent=Decimal("10.00"),
        image_url=None,
        is_active=True,
        is_visible=True,
        starts_at=None,
        ends_at=None,
        products=[],
        created_at=now,
        updated_at=now,
    )

    async def _list(self):
        return [deal]

    async def _get(self, slug: str):
        return deal

    monkeypatch.setattr("app.services.deal.DealService.list_public", _list)
    monkeypatch.setattr("app.services.deal.DealService.get_by_slug", _get)

    with TestClient(app) as client:
        assert client.get("/api/v1/deals").json()["data"][0]["slug"] == "family-feast"
        assert client.get("/api/v1/deals/family-feast").status_code == 200


def test_admin_category_requires_owner(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    customer = _user(role=UserRole.CUSTOMER)
    owner = _user(role=UserRole.CHEF)
    cat = _category()

    async def _create(self, payload):
        return cat

    monkeypatch.setattr("app.services.category.CategoryService.create", _create)

    _override_auth(app, customer)
    with TestClient(app) as client:
        denied = client.post("/api/v1/admin/categories", json={"name": "Pizza"})
        assert denied.status_code == 403

    app.dependency_overrides.clear()
    _override_auth(app, owner)
    with TestClient(app) as client:
        allowed = client.post("/api/v1/admin/categories", json={"name": "Pizza", "slug": "pizza"})
        assert allowed.status_code == 201
        assert allowed.json()["data"]["slug"] == "pizza"
    app.dependency_overrides.clear()


def test_admin_product_and_image_flow(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    owner = _user(role=UserRole.CHEF)
    _override_auth(app, owner)
    product_id = uuid4()
    item = _product_list_item()
    detail = ProductDetailResponse(
        **{**item.model_dump(), "id": product_id},
        description="x",
        is_visible=True,
        seo_title=None,
        seo_description=None,
        seo_keywords=None,
        updated_at=datetime.now(UTC),
        images=[],
        variants=[],
        extras=[],
        category=None,
    )
    image = ProductImageResponse(
        id=uuid4(),
        image_url="https://res.cloudinary.com/demo/image/upload/v1/p.jpg",
        public_id="prime_pizza/products/x",
        alt_text="front",
        is_primary=True,
        display_order=0,
        created_at=datetime.now(UTC),
    )

    async def _create(self, payload):
        assert payload.base_price == Decimal("999.00")
        return detail

    async def _upload(self, pid, **kwargs):
        assert pid == product_id
        return image

    async def _delete_image(self, pid, image_id):
        return None

    async def _reorder(self, pid, payload):
        return [image]

    monkeypatch.setattr("app.services.product.ProductService.create", _create)
    monkeypatch.setattr("app.services.product_image.ProductImageService.upload", _upload)
    monkeypatch.setattr("app.services.product_image.ProductImageService.delete", _delete_image)
    monkeypatch.setattr("app.services.product_image.ProductImageService.reorder", _reorder)

    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/admin/products",
            json={
                "category_id": str(uuid4()),
                "name": "Margherita",
                "base_price": "999.00",
                "variants": [
                    {"size": "medium", "name": "Medium", "price": "999.00"},
                ],
            },
        )
        assert created.status_code == 201

        upload = client.post(
            f"/api/v1/admin/products/{product_id}/images",
            files={"file": ("pizza.jpg", BytesIO(jpeg), "image/jpeg")},
            data={"is_primary": "true"},
        )
        assert upload.status_code == 201

        reorder = client.patch(
            f"/api/v1/admin/products/{product_id}/images/reorder",
            json={"image_ids": [str(image.id)]},
        )
        assert reorder.status_code == 200

        deleted = client.delete(f"/api/v1/admin/products/{product_id}/images/{image.id}")
        assert deleted.status_code == 200

    app.dependency_overrides.clear()


def test_admin_deal_crud(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    owner = _user(role=UserRole.CHEF)
    _override_auth(app, owner)
    now = datetime.now(UTC)
    deal_id = uuid4()
    deal = DealResponse(
        id=deal_id,
        name="Weekend Combo",
        slug="weekend-combo",
        description=None,
        deal_type=DealType.WEEKEND,
        deal_price=Decimal("1999.00"),
        discount_percent=None,
        image_url=None,
        is_active=True,
        is_visible=True,
        starts_at=None,
        ends_at=None,
        products=[],
        created_at=now,
        updated_at=now,
    )

    async def _create(self, payload):
        return deal

    async def _update(self, did, payload):
        return deal.model_copy(update={"name": payload.name or deal.name})

    async def _delete(self, did):
        return None

    monkeypatch.setattr("app.services.deal.DealService.create", _create)
    monkeypatch.setattr("app.services.deal.DealService.update", _update)
    monkeypatch.setattr("app.services.deal.DealService.delete", _delete)

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/admin/deals",
            json={"name": "Weekend Combo", "deal_type": "weekend", "deal_price": "1999.00"},
        )
        assert created.status_code == 201
        updated = client.patch(f"/api/v1/admin/deals/{deal_id}", json={"name": "Weekend Combo+"})
        assert updated.status_code == 200
        deleted = client.delete(f"/api/v1/admin/deals/{deal_id}")
        assert deleted.status_code == 200

    app.dependency_overrides.clear()


def test_product_validation_rejects_bad_discount() -> None:
    app = create_app(settings=get_settings())
    owner = _user(role=UserRole.CHEF)
    _override_auth(app, owner)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/admin/products",
            json={
                "category_id": str(uuid4()),
                "name": "Bad Deal",
                "base_price": "100.00",
                "discount_price": "150.00",
            },
        )
        assert response.status_code == 422
    app.dependency_overrides.clear()

