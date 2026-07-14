"""Address management service."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization.ownership import OwnershipService
from app.config.settings import Settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.user import Address, User
from app.repositories.address import AddressRepository
from app.schemas.users import AddressCreateRequest, AddressResponse, AddressUpdateRequest
from app.services.base import BaseService


class AddressService(BaseService):
    service_name = "address"

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        ownership: OwnershipService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._addresses = AddressRepository(session)
        self._ownership = ownership or OwnershipService()

    async def list_addresses(self, user: User) -> list[AddressResponse]:
        rows = await self._addresses.list_for_user(user.id)
        return [AddressResponse.model_validate(row) for row in rows]

    async def create_address(self, user: User, payload: AddressCreateRequest) -> AddressResponse:
        count = await self._addresses.count_for_user(user.id)
        if count >= self._settings.max_addresses_per_user:
            raise ValidationException(
                f"Maximum of {self._settings.max_addresses_per_user} addresses allowed",
            )

        if payload.is_default or count == 0:
            await self._addresses.clear_defaults(user.id)
            is_default = True
        else:
            is_default = False

        address = Address(
            user_id=user.id,
            title=payload.title,
            recipient_name=payload.recipient_name,
            phone_number=payload.phone_number,
            street=payload.street,
            area=payload.area,
            city=payload.city,
            province=payload.province,
            postal_code=payload.postal_code,
            country=payload.country,
            latitude=payload.latitude,
            longitude=payload.longitude,
            delivery_notes=payload.delivery_notes,
            is_default=is_default,
        )
        await self._addresses.add(address)
        await self._session.commit()
        await self._session.refresh(address)
        logger.info("Address added | user_id={} | address_id={}", user.id, address.id)
        return AddressResponse.model_validate(address)

    async def update_address(
        self,
        user: User,
        address_id: UUID,
        payload: AddressUpdateRequest,
    ) -> AddressResponse:
        address = await self._get_owned(user, address_id)
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No address fields provided")

        if data.get("is_default") is True:
            await self._addresses.clear_defaults(user.id)

        for key, value in data.items():
            setattr(address, key, value)

        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(address)
        logger.info("Address updated | user_id={} | address_id={}", user.id, address.id)
        return AddressResponse.model_validate(address)

    async def delete_address(self, user: User, address_id: UUID) -> None:
        address = await self._get_owned(user, address_id)
        was_default = address.is_default
        await self._addresses.soft_delete(address)
        await self._session.flush()

        if was_default:
            remaining = await self._addresses.list_for_user(user.id)
            if remaining:
                remaining[0].is_default = True
                await self._session.flush()

        await self._session.commit()
        logger.info("Address deleted | user_id={} | address_id={}", user.id, address_id)

    async def set_default(self, user: User, address_id: UUID) -> AddressResponse:
        address = await self._get_owned(user, address_id)
        await self._addresses.clear_defaults(user.id)
        address.is_default = True
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(address)
        logger.info("Address set default | user_id={} | address_id={}", user.id, address_id)
        return AddressResponse.model_validate(address)

    async def _get_owned(self, user: User, address_id: UUID) -> Address:
        address = await self._addresses.get_for_user(address_id, user.id)
        if address is None:
            # Hide existence of other users' addresses
            raise NotFoundException("Address not found")
        self._ownership.ensure_owner_or_self(user, address.user_id, resource_name="address")
        return address
