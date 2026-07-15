"""Owner email testing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.authorization.permissions import Permission
from app.common.enums import EmailDeliveryStatus
from app.core.exceptions import ExternalServiceException
from app.dependencies.authorization import require_permission
from app.dependencies.email import get_email_service
from app.models.user import User
from app.schemas.emails import TestEmailRequest, TestEmailResponse
from app.schemas.response import SuccessResponse
from app.services.email import EmailService

router = APIRouter(prefix="/admin", tags=["Admin Email"])


@router.post("/test-email", response_model=SuccessResponse[TestEmailResponse])
async def send_test_email(
    request: Request,
    body: TestEmailRequest | None = None,
    _: User = Depends(require_permission(Permission.EMAIL_TEST)),
    service: EmailService = Depends(get_email_service),
) -> SuccessResponse[TestEmailResponse]:
    payload = body or TestEmailRequest()
    log = await service.send_owner_test(
        to=str(payload.to) if payload.to else None,
        message=payload.message,
    )
    if log.status != EmailDeliveryStatus.SENT:
        raise ExternalServiceException(
            f"Test email did not send successfully (status={log.status.value})",
            service="brevo",
            details={
                "status": log.status.value,
                "failure_reason": log.failure_reason,
                "email_log_id": str(log.id),
            },
        )

    recipients = (log.meta or {}).get("recipients") or [log.recipient]
    data = TestEmailResponse(
        queued=True,
        recipients=recipients,
        subject=log.subject,
        status=log.status,
        email_log_id=log.id,
        detail="Test email sent successfully",
    )
    return SuccessResponse(
        success=True,
        message="Test email sent successfully",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
