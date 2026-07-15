"""User repository with search helpers and admin listing."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserRole
from app.models.order import Order
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.admin_customers import AdminCustomerFilterParams


class UserRepository(BaseRepository[User]):
    """Data-access boundary for User authentication / profile / admin flows."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_phone(self, phone_number: str) -> User | None:
        stmt = select(User).where(
            User.phone_number == phone_number,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            User.email == email.strip().lower(),
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        """Search across phone, email, and name."""
        pattern = f"%{query.strip()}%"
        stmt = (
            select(User)
            .where(
                User.deleted_at.is_(None),
                or_(
                    User.phone_number.ilike(pattern),
                    User.email.ilike(pattern),
                    User.full_name.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                ),
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_phone(self, phone_number: str) -> list[User]:
        stmt = select(User).where(
            User.deleted_at.is_(None),
            User.phone_number.ilike(f"%{phone_number.strip()}%"),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_email(self, email: str) -> list[User]:
        stmt = select(User).where(
            User.deleted_at.is_(None),
            User.email.ilike(f"%{email.strip()}%"),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(self, name: str) -> list[User]:
        stmt = select(User).where(
            User.deleted_at.is_(None),
            or_(
                User.full_name.ilike(f"%{name.strip()}%"),
                User.first_name.ilike(f"%{name.strip()}%"),
                User.last_name.ilike(f"%{name.strip()}%"),
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _apply_admin_filters(self, stmt: Select, filters: AdminCustomerFilterParams) -> Select:
        stmt = stmt.where(User.deleted_at.is_(None))
        if filters.role is not None:
            stmt = stmt.where(User.role == filters.role)
        else:
            stmt = stmt.where(User.role == UserRole.CUSTOMER)
        if filters.is_active is not None:
            stmt = stmt.where(User.is_active.is_(filters.is_active))
        if filters.is_verified is not None:
            stmt = stmt.where(User.is_verified.is_(filters.is_verified))
        if filters.date_from is not None:
            stmt = stmt.where(User.created_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(User.created_at <= filters.date_to)
        if filters.name:
            pattern = f"%{filters.name.strip()}%"
            stmt = stmt.where(
                or_(
                    User.full_name.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )
        if filters.phone:
            stmt = stmt.where(User.phone_number.ilike(f"%{filters.phone.strip()}%"))
        if filters.email:
            stmt = stmt.where(User.email.ilike(f"%{filters.email.strip()}%"))
        if filters.q:
            pattern = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(
                    User.full_name.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.phone_number.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if filters.sort == "oldest":
            stmt = stmt.order_by(User.created_at.asc())
        elif filters.sort == "name":
            stmt = stmt.order_by(User.full_name.asc().nullslast(), User.created_at.desc())
        else:
            stmt = stmt.order_by(User.created_at.desc())
        return stmt

    async def list_admin_filtered(
        self,
        filters: AdminCustomerFilterParams,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[User], int]:
        base = select(User)
        base = self._apply_admin_filters(base, filters)
        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def count_orders_for_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Order).where(
            Order.user_id == user_id,
            Order.deleted_at.is_(None),
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_ids_by_role(self, role: UserRole | None = UserRole.CUSTOMER) -> list[UUID]:
        stmt = select(User.id).where(User.deleted_at.is_(None), User.is_active.is_(True))
        if role is not None:
            stmt = stmt.where(User.role == role)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_registered_user(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
        role: UserRole,
        phone_number: str | None = None,
    ) -> User:
        full_name = f"{first_name.strip()} {last_name.strip()}".strip()
        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            full_name=full_name,
            email=email.strip().lower(),
            password_hash=password_hash,
            phone_number=phone_number,
            role=role,
            is_active=True,
            is_verified=True,
            last_login=datetime.now(UTC),
        )
        return await self.add(user)

    async def create_user(
        self,
        *,
        phone_number: str | None,
        role: UserRole,
        full_name: str | None = None,
        email: str | None = None,
        password_hash: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """Legacy helper — prefer create_registered_user for email/password signup."""
        fn = (first_name or "").strip() or ("Kitchen" if role == UserRole.CHEF else "Customer")
        ln = (last_name or "").strip() or ("Chef" if role == UserRole.CHEF else "")
        display = full_name or f"{fn} {ln}".strip()
        if not email:
            msg = "email is required when creating a user"
            raise ValueError(msg)
        if not password_hash:
            msg = "password_hash is required when creating a user"
            raise ValueError(msg)
        return await self.create_registered_user(
            first_name=fn,
            last_name=ln or "User",
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
            role=role,
        )

    async def create_customer(
        self,
        *,
        phone_number: str | None = None,
        full_name: str | None = None,
        email: str,
        password_hash: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        return await self.create_user(
            phone_number=phone_number,
            role=UserRole.CUSTOMER,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

    async def mark_login(self, user: User, *, role: UserRole | None = None) -> User:
        user.last_login = datetime.now(UTC)
        user.is_verified = True
        if role is not None and user.role != role:
            user.role = role
        await self.session.flush()
        return user

    async def deactivate(self, user: User) -> User:
        user.is_active = False
        await self.session.flush()
        return user

    async def soft_delete_account(self, user: User) -> User:
        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return user
