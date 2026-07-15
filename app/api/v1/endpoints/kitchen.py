"""Kitchen dashboard APIs — chef role required on every route."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import APIMessages
from app.dependencies.auth import get_current_chef
from app.dependencies.database import get_db_session
from app.dependencies.orders import get_order_service
from app.models.user import User
from app.schemas.kitchen import (
    KitchenActionRequest,
    KitchenBoardResponse,
    KitchenOrderCardResponse,
    KitchenStatusUpdateRequest,
)
from app.schemas.response import SuccessResponse
from app.services.kitchen import KitchenService
from app.services.order import OrderService


def get_kitchen_service(
    session: AsyncSession = Depends(get_db_session),
    order_service: OrderService = Depends(get_order_service),
) -> KitchenService:
    return KitchenService(session=session, order_service=order_service)


def build_kitchen_router(*, prefix: str, tags: list[str] | None = None) -> APIRouter:
    """Build a kitchen router under any chef-facing URL prefix."""
    router = APIRouter(prefix=prefix, tags=tags or ["Kitchen Dashboard"])

    @router.get(
        "/orders",
        response_model=SuccessResponse[KitchenBoardResponse],
        summary="Kitchen order boards",
        description=(
            "Returns pending/incoming, preparing, ready, completed, and cancelled "
            "orders for the chef kitchen dashboard."
        ),
    )
    async def kitchen_boards(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenBoardResponse]:
        data = await service.get_board()
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/pending",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Pending kitchen orders",
    )
    async def kitchen_pending(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("pending")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/incoming",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Incoming kitchen orders",
    )
    async def kitchen_incoming(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("incoming")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/preparing",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Preparing kitchen orders",
    )
    async def kitchen_preparing(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("preparing")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/ready",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Ready kitchen orders",
    )
    async def kitchen_ready(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("ready")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/completed",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Completed kitchen orders",
    )
    async def kitchen_completed(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("completed")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/cancelled",
        response_model=SuccessResponse[list[KitchenOrderCardResponse]],
        summary="Cancelled kitchen orders",
    )
    async def kitchen_cancelled(
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[list[KitchenOrderCardResponse]]:
        data = await service.list_status("cancelled")
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.get(
        "/orders/{order_id}",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Kitchen order details",
    )
    async def kitchen_order_detail(
        order_id: UUID,
        request: Request,
        _: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.get_order(order_id)
        return SuccessResponse(
            success=True,
            message=APIMessages.SUCCESS,
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.patch(
        "/orders/{order_id}/status",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Update kitchen order status",
        description="Chef-only status updates: pending, preparing, ready, completed.",
    )
    async def update_kitchen_status(
        order_id: UUID,
        body: KitchenStatusUpdateRequest,
        request: Request,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.update_status(chef, order_id, body)
        return SuccessResponse(
            success=True,
            message=f"Order status updated to {body.status}",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.post(
        "/orders/{order_id}/accept",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        status_code=status.HTTP_200_OK,
        summary="Accept incoming order",
    )
    async def accept_order(
        order_id: UUID,
        request: Request,
        body: KitchenActionRequest | None = None,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.apply_action(chef, order_id, "accept", body)
        return SuccessResponse(
            success=True,
            message="Order accepted",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.post(
        "/orders/{order_id}/start-preparing",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Start preparing order",
    )
    async def start_preparing(
        order_id: UUID,
        request: Request,
        body: KitchenActionRequest | None = None,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.apply_action(chef, order_id, "start-preparing", body)
        return SuccessResponse(
            success=True,
            message="Order is being prepared",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.post(
        "/orders/{order_id}/mark-ready",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Mark order ready",
    )
    async def mark_ready(
        order_id: UUID,
        request: Request,
        body: KitchenActionRequest | None = None,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.apply_action(chef, order_id, "mark-ready", body)
        return SuccessResponse(
            success=True,
            message="Order marked ready",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.post(
        "/orders/{order_id}/complete",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Complete order",
    )
    async def complete_order(
        order_id: UUID,
        request: Request,
        body: KitchenActionRequest | None = None,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.apply_action(chef, order_id, "complete", body)
        return SuccessResponse(
            success=True,
            message="Order completed",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    @router.post(
        "/orders/{order_id}/cancel",
        response_model=SuccessResponse[KitchenOrderCardResponse],
        summary="Cancel order",
    )
    async def cancel_order(
        order_id: UUID,
        request: Request,
        body: KitchenActionRequest | None = None,
        chef: User = Depends(get_current_chef),
        service: KitchenService = Depends(get_kitchen_service),
    ) -> SuccessResponse[KitchenOrderCardResponse]:
        data = await service.apply_action(chef, order_id, "cancel", body)
        return SuccessResponse(
            success=True,
            message="Order cancelled",
            data=data,
            request_id=getattr(request.state, "request_id", None),
        )

    return router


# Canonical kitchen routes
router = build_kitchen_router(prefix="/kitchen", tags=["Kitchen Dashboard"])

# Frontend-compatible aliases (same handlers / same chef authorization)
chef_router = build_kitchen_router(prefix="/chef", tags=["Chef Dashboard"])
orders_kitchen_router = build_kitchen_router(
    prefix="/orders/kitchen",
    tags=["Kitchen Orders"],
)
dashboard_chef_router = build_kitchen_router(
    prefix="/dashboard/chef",
    tags=["Chef Dashboard"],
)
