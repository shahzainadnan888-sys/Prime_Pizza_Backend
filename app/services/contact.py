"""Contact form business logic."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.contact_message import ContactMessageRepository
from app.schemas.contact import ContactMessageCreate, ContactMessageResponse
from app.services.base import BaseService
from app.services.email_service import EmailService


class ContactService(BaseService):
    service_name = "contact"

    def __init__(
        self,
        *,
        session: AsyncSession,
        email_service: EmailService,
    ) -> None:
        self._session = session
        self._repo = ContactMessageRepository(session)
        self._email = email_service

    async def submit(
        self,
        payload: ContactMessageCreate,
        *,
        client_ip: str | None = None,
    ) -> ContactMessageResponse:
        row = await self._repo.create_message(
            name=payload.name,
            email=str(payload.email),
            phone=payload.phone,
            subject=payload.subject,
            message=payload.message,
        )
        await self._session.commit()
        await self._session.refresh(row)
        logger.info(
            "Contact message saved | id={} | email={} | ip={}",
            row.id,
            row.email,
            client_ip,
        )

        # Persist first; admin inbox email is awaited (502 on Brevo failure).
        await self._email.notify_contact_submission(
            name=row.name,
            email=row.email,
            phone=row.phone,
            subject=row.subject,
            message=row.message,
            submission_time=row.created_at,
            client_ip=client_ip,
        )

        return ContactMessageResponse.model_validate(row)
