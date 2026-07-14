"""Unit tests for catalog helpers and validation."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from uuid import uuid4

import pytest
from app.common.enums import ProductTag, VariantSize
from app.config.settings import get_settings
from app.core.exceptions import ValidationException
from app.schemas.catalog import ProductCreateRequest, ProductFilterParams, VariantCreateRequest
from app.services.cloudinary_catalog import CatalogCloudinaryService
from app.utils.slug import slugify
from pydantic import ValidationError


def test_slugify() -> None:
    assert slugify("Cheese Burst Pizza!") == "cheese-burst-pizza"
    with pytest.raises(ValueError):
        slugify("???")


def test_product_create_validates_discount() -> None:
    ProductCreateRequest(
        category_id=uuid4(),
        name="Margherita",
        base_price=Decimal("500"),
        discount_price=Decimal("400"),
        tags=[ProductTag.VEGETARIAN],
        variants=[VariantCreateRequest(size=VariantSize.MEDIUM, name="Medium", price=Decimal("500"))],
    )
    with pytest.raises(ValidationError):
        ProductCreateRequest(
            category_id=uuid4(),
            name="Bad",
            base_price=Decimal("100"),
            discount_price=Decimal("200"),
        )


def test_filter_params_price_range() -> None:
    with pytest.raises(ValidationError):
        ProductFilterParams(min_price=Decimal("200"), max_price=Decimal("100"))


def test_catalog_cloudinary_validation() -> None:
    service = CatalogCloudinaryService(get_settings())
    with pytest.raises(ValidationException):
        service.validate_upload(filename="x.exe", content_type="image/jpeg", size=10)
    with pytest.raises(ValidationException):
        service.validate_upload(
            filename="x.jpg",
            content_type="image/jpeg",
            size=get_settings().product_image_max_bytes + 1,
        )
    service.validate_upload(filename="x.jpg", content_type="image/jpeg", size=100)
    assert service.validate_upload  # callable sanity
    fake = BytesIO(b"not-image")
    with pytest.raises(ValidationException):
        service.upload(
            file_obj=fake,
            folder="test",
            public_id=None,
            filename="x.jpg",
            content_type="image/jpeg",
            size=9,
        )
