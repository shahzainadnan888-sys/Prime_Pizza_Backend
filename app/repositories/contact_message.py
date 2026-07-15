"""Contact message persistence."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_message import ContactMessage
from app.repositories.base import BaseRepository


class ContactMessageRepository(BaseRepository[ContactMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ContactMessage)

    async def create_message(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        subject: str,
        message: str,
    ) -> ContactMessage:
        row = ContactMessage(
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None,
            subject=subject.strip(),
            message=message.strip(),
            is_resolved=False,
        )
        return await self.add(row)
