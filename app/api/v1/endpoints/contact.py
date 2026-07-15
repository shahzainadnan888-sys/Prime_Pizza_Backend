"""Public contact form API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.dependencies.email import get_email_service
from app.schemas.contact import ContactMessageCreate, ContactMessageResponse
from app.schemas.response import SuccessResponse
from app.services.contact import ContactService
from app.services.email_service import EmailService
from app.utils.network import get_client_ip

router = APIRouter(tags=["Contact"])


def get_contact_service(
    session: AsyncSession = Depends(get_db_session),
    email_service: EmailService = Depends(get_email_service),
) -> ContactService:
    return ContactService(session=session, email_service=email_service)


async def _submit(
    body: ContactMessageCreate,
    request: Request,
    service: ContactService,
) -> SuccessResponse[ContactMessageResponse]:
    data = await service.submit(body, client_ip=get_client_ip(request))
    return SuccessResponse(
        success=True,
        message="Thank you — your message has been received",
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


_CONTACT_DESCRIPTION = (
    "Stores the inquiry in PostgreSQL and emails CONTACT_RECEIVER_EMAIL via Brevo "
    "after commit. Required admin email failure returns HTTP 502."
)


@router.post(
    "/contact",
    response_model=SuccessResponse[ContactMessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit contact form",
    description=_CONTACT_DESCRIPTION,
)
@router.post(
    "/contact/",
    response_model=SuccessResponse[ContactMessageResponse],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/contacts",
    response_model=SuccessResponse[ContactMessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit contact form (alias)",
    description=_CONTACT_DESCRIPTION,
    include_in_schema=False,
)
async def submit_contact(
    body: ContactMessageCreate,
    request: Request,
    service: ContactService = Depends(get_contact_service),
) -> SuccessResponse[ContactMessageResponse]:
    return await _submit(body, request, service)
