"""User management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.common.constants import APIMessages
from app.dependencies.authorization import require_verified
from app.dependencies.users import (
    get_address_service,
    get_preference_service,
    get_user_notification_service,
    get_user_service,
)
from app.models.user import User
from app.schemas.response import MessageResponse, SuccessResponse
from app.schemas.users import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
    AvatarUploadResponse,
    NotificationResponse,
    PreferenceResponse,
    PreferenceUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.services.address import AddressService
from app.services.notification import UserNotificationService
from app.services.preference import PreferenceService
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse[UserProfileResponse])
async def get_my_profile(
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserProfileResponse]:
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=service.get_profile(user),
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/me", response_model=SuccessResponse[UserProfileResponse])
async def update_my_profile(
    body: UserProfileUpdateRequest,
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserProfileResponse]:
    data = await service.update_profile(user, body)
    return SuccessResponse(
        success=True,
        message="Profile updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/avatar", response_model=SuccessResponse[AvatarUploadResponse])
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[AvatarUploadResponse]:
    from io import BytesIO

    from app.utils.uploads import read_upload_limited, safe_upload_filename

    content = await read_upload_limited(
        file,
        max_bytes=request.app.state.settings.avatar_max_bytes,
    )
    data = await service.upload_avatar(
        user,
        file_obj=BytesIO(content),
        filename=safe_upload_filename(file.filename, default="avatar.jpg"),
        content_type=file.content_type,
        size=len(content),
    )
    return SuccessResponse(
        success=True,
        message="Avatar uploaded",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/avatar", response_model=SuccessResponse[UserProfileResponse])
async def delete_avatar(
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserProfileResponse]:
    data = await service.delete_avatar(user)
    return SuccessResponse(
        success=True,
        message="Avatar deleted",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/me/deactivate", response_model=SuccessResponse[UserProfileResponse])
async def deactivate_account(
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserProfileResponse]:
    data = await service.deactivate_account(user)
    return SuccessResponse(
        success=True,
        message="Account deactivated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/me", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def soft_delete_account(
    request: Request,
    user: User = Depends(require_verified),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    await service.soft_delete_account(user)
    return MessageResponse(
        success=True,
        message="Account deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/addresses", response_model=SuccessResponse[list[AddressResponse]])
async def list_addresses(
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> SuccessResponse[list[AddressResponse]]:
    data = await service.list_addresses(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/addresses",
    response_model=SuccessResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
    body: AddressCreateRequest,
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> SuccessResponse[AddressResponse]:
    data = await service.create_address(user, body)
    return SuccessResponse(
        success=True,
        message="Address added",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/addresses/{address_id}", response_model=SuccessResponse[AddressResponse])
async def update_address(
    address_id: UUID,
    body: AddressUpdateRequest,
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> SuccessResponse[AddressResponse]:
    data = await service.update_address(user, address_id, body)
    return SuccessResponse(
        success=True,
        message="Address updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: UUID,
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> MessageResponse:
    await service.delete_address(user, address_id)
    return MessageResponse(
        success=True,
        message="Address deleted",
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/addresses/{address_id}/default",
    response_model=SuccessResponse[AddressResponse],
)
async def set_default_address(
    address_id: UUID,
    request: Request,
    user: User = Depends(require_verified),
    service: AddressService = Depends(get_address_service),
) -> SuccessResponse[AddressResponse]:
    data = await service.set_default(user, address_id)
    return SuccessResponse(
        success=True,
        message="Default address updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/preferences", response_model=SuccessResponse[PreferenceResponse])
async def get_preferences(
    request: Request,
    user: User = Depends(require_verified),
    service: PreferenceService = Depends(get_preference_service),
) -> SuccessResponse[PreferenceResponse]:
    data = await service.get_preferences(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/preferences", response_model=SuccessResponse[PreferenceResponse])
async def update_preferences(
    body: PreferenceUpdateRequest,
    request: Request,
    user: User = Depends(require_verified),
    service: PreferenceService = Depends(get_preference_service),
) -> SuccessResponse[PreferenceResponse]:
    data = await service.update_preferences(user, body)
    return SuccessResponse(
        success=True,
        message="Preferences updated",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/notifications", response_model=SuccessResponse[list[NotificationResponse]])
async def list_notifications(
    request: Request,
    user: User = Depends(require_verified),
    service: UserNotificationService = Depends(get_user_notification_service),
) -> SuccessResponse[list[NotificationResponse]]:
    data = await service.list_notifications(user)
    return SuccessResponse(
        success=True,
        message=APIMessages.SUCCESS,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/notifications/read-all", response_model=MessageResponse)
async def mark_all_notifications_read(
    request: Request,
    user: User = Depends(require_verified),
    service: UserNotificationService = Depends(get_user_notification_service),
) -> MessageResponse:
    count = await service.mark_all_read(user)
    return MessageResponse(
        success=True,
        message=f"Marked {count} notifications as read",
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=SuccessResponse[NotificationResponse],
)
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    user: User = Depends(require_verified),
    service: UserNotificationService = Depends(get_user_notification_service),
) -> SuccessResponse[NotificationResponse]:
    data = await service.mark_read(user, notification_id)
    return SuccessResponse(
        success=True,
        message="Notification marked as read",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/notifications/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: UUID,
    request: Request,
    user: User = Depends(require_verified),
    service: UserNotificationService = Depends(get_user_notification_service),
) -> MessageResponse:
    await service.delete_notification(user, notification_id)
    return MessageResponse(
        success=True,
        message="Notification deleted",
        request_id=getattr(request.state, "request_id", None),
    )
