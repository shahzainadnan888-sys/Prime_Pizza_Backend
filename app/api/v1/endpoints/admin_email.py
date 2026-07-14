"""Owner email testing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.authorization.permissions import Permission
from app.common.enums import EmailDeliveryStatus
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
    detail = "Test email sent"
    if log.status == EmailDeliveryStatus.SKIPPED:
        detail = "Email skipped — configure RESEND_API_KEY and EMAIL_ENABLED"
    elif log.status == EmailDeliveryStatus.FAILED:
        detail = "Test email failed after retries"
    elif log.status == EmailDeliveryStatus.SENT:
        detail = "Test email sent successfully"

    recipients = (log.meta or {}).get("recipients") or [log.recipient]
    data = TestEmailResponse(
        queued=log.status
        in {EmailDeliveryStatus.QUEUED, EmailDeliveryStatus.SENDING, EmailDeliveryStatus.SENT},
        recipients=recipients,
        subject=log.subject,
        status=log.status,
        email_log_id=log.id,
        detail=detail,
    )
    return SuccessResponse(
        success=True,
        message=detail,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )
