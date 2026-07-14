"""Owner-only catalog administration APIs."""

from __future__ import annotations

from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.authorization.permissions import Permission
from app.dependencies.authorization import require_permission
from app.dependencies.catalog import (
    get_category_service,
    get_deal_service,
    get_product_image_service,
    get_product_service,
)
from app.models.user import User
from app.schemas.admin_catalog_ops import (
    BulkMutationResult,
    CategoryReorderRequest,
    DealScheduleRequest,
    ProductBulkAvailabilityRequest,
    ProductBulkCategoryRequest,
    ProductBulkDeleteRequest,
    ProductBulkFeaturedRequest,
    ProductBulkVisibilityRequest,
)
from app.schemas.catalog import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    DealCreateRequest,
    DealResponse,
    DealUpdateRequest,
    ImageReorderRequest,
    ProductCreateRequest,
    ProductDetailResponse,
    ProductImageResponse,
    ProductUpdateRequest,
)
from app.schemas.response import MessageResponse, SuccessResponse
from app.services.category import CategoryService
from app.services.deal import DealService
from app.services.product import ProductService
from app.services.product_image import ProductImageService

router = APIRouter(prefix="/admin", tags=["Admin Catalog"])


@router.post(
    "/categories",
    response_model=SuccessResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    body: CategoryCreateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_CREATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[CategoryResponse]:
    data = await service.create(body)
    return SuccessResponse(
        success=True,
        message="Category created",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/categories", response_model=SuccessResponse[list[CategoryResponse]])
async def list_admin_categories(
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_UPDATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[list[CategoryResponse]]:
    data = await service.list_admin()
    return SuccessResponse(
        success=True,
        message="Categories listed",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/categories/reorder",
    response_model=SuccessResponse[list[CategoryResponse]],
)
async def reorder_categories(
    body: CategoryReorderRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_UPDATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[list[CategoryResponse]]:
    items = [(item.category_id, item.display_order) for item in body.items]
    data = await service.reorder(items)
    return SuccessResponse(
        success=True,
        message="Categories reordered",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/categories/{category_id}", response_model=SuccessResponse[CategoryResponse])
async def update_category(
    category_id: UUID,
    body: CategoryUpdateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_UPDATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[CategoryResponse]:
    data = await service.update(category_id, body)
    return SuccessResponse(
        success=True,
        message="Category updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_DELETE)),
    service: CategoryService = Depends(get_category_service),
) -> MessageResponse:
    await service.delete(category_id)
    return MessageResponse(
        success=True,
        message="Category deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/categories/{category_id}/hide",
    response_model=SuccessResponse[CategoryResponse],
)
async def hide_category(
    category_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_UPDATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[CategoryResponse]:
    data = await service.hide(category_id)
    return SuccessResponse(
        success=True,
        message="Category hidden",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/categories/{category_id}/restore",
    response_model=SuccessResponse[CategoryResponse],
)
async def restore_category(
    category_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.CATEGORY_UPDATE)),
    service: CategoryService = Depends(get_category_service),
) -> SuccessResponse[CategoryResponse]:
    data = await service.restore(category_id)
    return SuccessResponse(
        success=True,
        message="Category restored",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products",
    response_model=SuccessResponse[ProductDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    body: ProductCreateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_CREATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[ProductDetailResponse]:
    data = await service.create(body)
    return SuccessResponse(
        success=True,
        message="Product created",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/products/{product_id}", response_model=SuccessResponse[ProductDetailResponse])
async def update_product(
    product_id: UUID,
    body: ProductUpdateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[ProductDetailResponse]:
    data = await service.update(product_id, body)
    return SuccessResponse(
        success=True,
        message="Product updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_DELETE)),
    service: ProductService = Depends(get_product_service),
) -> MessageResponse:
    await service.delete(product_id)
    return MessageResponse(
        success=True,
        message="Product deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/{product_id}/images",
    response_model=SuccessResponse[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    is_primary: bool = Form(default=False),
    _: User = Depends(require_permission(Permission.IMAGE_UPLOAD)),
    service: ProductImageService = Depends(get_product_image_service),
) -> SuccessResponse[ProductImageResponse]:
    from app.utils.uploads import read_upload_limited, safe_upload_filename

    content = await read_upload_limited(
        file,
        max_bytes=request.app.state.settings.product_image_max_bytes,
    )
    data = await service.upload(
        product_id,
        file_obj=BytesIO(content),
        filename=safe_upload_filename(file.filename, default="product.jpg"),
        content_type=file.content_type,
        size=len(content),
        alt_text=alt_text,
        is_primary=is_primary,
    )
    return SuccessResponse(
        success=True,
        message="Image uploaded",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete(
    "/products/{product_id}/images/{image_id}",
    response_model=MessageResponse,
)
async def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.IMAGE_MANAGE)),
    service: ProductImageService = Depends(get_product_image_service),
) -> MessageResponse:
    await service.delete(product_id, image_id)
    return MessageResponse(
        success=True,
        message="Image deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/products/{product_id}/images/reorder",
    response_model=SuccessResponse[list[ProductImageResponse]],
)
async def reorder_product_images(
    product_id: UUID,
    body: ImageReorderRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.IMAGE_MANAGE)),
    service: ProductImageService = Depends(get_product_image_service),
) -> SuccessResponse[list[ProductImageResponse]]:
    data = await service.reorder(product_id, body)
    return SuccessResponse(
        success=True,
        message="Images reordered",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/deals",
    response_model=SuccessResponse[DealResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_deal(
    body: DealCreateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_CREATE)),
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.create(body)
    return SuccessResponse(
        success=True,
        message="Deal created",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/deals/{deal_id}", response_model=SuccessResponse[DealResponse])
async def update_deal(
    deal_id: UUID,
    body: DealUpdateRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_UPDATE)),
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.update(deal_id, body)
    return SuccessResponse(
        success=True,
        message="Deal updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/deals/{deal_id}", response_model=MessageResponse)
async def delete_deal(
    deal_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_DELETE)),
    service: DealService = Depends(get_deal_service),
) -> MessageResponse:
    await service.delete(deal_id)
    return MessageResponse(
        success=True,
        message="Deal deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/bulk/visibility",
    response_model=SuccessResponse[BulkMutationResult],
)
async def bulk_product_visibility(
    body: ProductBulkVisibilityRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[BulkMutationResult]:
    matched, updated = await service.bulk_update_fields(
        body.product_ids,
        fields={"is_visible": body.is_visible},
    )
    return SuccessResponse(
        success=True,
        message="Products visibility updated",
        data=BulkMutationResult(matched=matched, updated=updated),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/bulk/featured",
    response_model=SuccessResponse[BulkMutationResult],
)
async def bulk_product_featured(
    body: ProductBulkFeaturedRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[BulkMutationResult]:
    matched, updated = await service.bulk_update_fields(
        body.product_ids,
        fields={"is_featured": body.is_featured},
    )
    return SuccessResponse(
        success=True,
        message="Products featured flag updated",
        data=BulkMutationResult(matched=matched, updated=updated),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/bulk/availability",
    response_model=SuccessResponse[BulkMutationResult],
)
async def bulk_product_availability(
    body: ProductBulkAvailabilityRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[BulkMutationResult]:
    matched, updated = await service.bulk_update_fields(
        body.product_ids,
        fields={"is_available": body.is_available},
    )
    return SuccessResponse(
        success=True,
        message="Products availability updated",
        data=BulkMutationResult(matched=matched, updated=updated),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/bulk/category",
    response_model=SuccessResponse[BulkMutationResult],
)
async def bulk_product_category(
    body: ProductBulkCategoryRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[BulkMutationResult]:
    matched, updated = await service.bulk_update_fields(
        body.product_ids,
        fields={"category_id": body.category_id},
    )
    return SuccessResponse(
        success=True,
        message="Products category updated",
        data=BulkMutationResult(matched=matched, updated=updated),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/products/bulk/delete",
    response_model=SuccessResponse[BulkMutationResult],
)
async def bulk_product_delete(
    body: ProductBulkDeleteRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.PRODUCT_DELETE)),
    service: ProductService = Depends(get_product_service),
) -> SuccessResponse[BulkMutationResult]:
    matched, updated = await service.bulk_delete(body.product_ids)
    return SuccessResponse(
        success=True,
        message="Products deleted",
        data=BulkMutationResult(matched=matched, updated=updated),
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/deals/{deal_id}/activate", response_model=SuccessResponse[DealResponse])
async def activate_deal(
    deal_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_UPDATE)),
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.set_active(deal_id, is_active=True)
    return SuccessResponse(
        success=True,
        message="Deal activated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/deals/{deal_id}/deactivate", response_model=SuccessResponse[DealResponse])
async def deactivate_deal(
    deal_id: UUID,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_UPDATE)),
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.set_active(deal_id, is_active=False)
    return SuccessResponse(
        success=True,
        message="Deal deactivated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/deals/{deal_id}/schedule", response_model=SuccessResponse[DealResponse])
async def schedule_deal(
    deal_id: UUID,
    body: DealScheduleRequest,
    request: Request,
    _: User = Depends(require_permission(Permission.DEAL_UPDATE)),
    service: DealService = Depends(get_deal_service),
) -> SuccessResponse[DealResponse]:
    data = await service.schedule(
        deal_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        is_active=body.is_active,
        is_visible=body.is_visible,
    )
    return SuccessResponse(
        success=True,
        message="Deal schedule updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
