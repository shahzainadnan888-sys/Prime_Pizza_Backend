"""Startup seeding helpers (schema, chef account, demo catalog)."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import CouponType, StockStatus
from app.config.settings import Settings
from app.models.catalog import Category, Product
from app.models.coupon import Coupon
from app.repositories.redis_auth import RedisAuthRepository
from app.security.jwt import JWTService
from app.services.auth import AuthService
from app.services.user_sync import UserSyncService
from app.utils.slug import slugify


def _run_alembic_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    command.upgrade(cfg, "head")


async def _create_all_tables(engine) -> None:
    """Fallback when Alembic cannot run — creates tables from SQLAlchemy metadata."""
    import app.models  # noqa: F401 — register all models on Base.metadata
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_schema_ready(settings: Settings) -> None:
    """
    Always apply Alembic migrations to head.

    Falls back to metadata.create_all only when the public schema is still empty
    after a migrate failure (local/dev safety net).
    """
    connect_args: dict = {"timeout": 15}
    if "neon.tech" in settings.database_url:
        connect_args["statement_cache_size"] = 0
        connect_args["command_timeout"] = 30

    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args=connect_args,
    )
    try:
        async with engine.connect() as conn:
            count = (
                await conn.execute(
                    text(
                        "select count(*) from information_schema.tables "
                        "where table_schema='public' and table_type='BASE TABLE'"
                    )
                )
            ).scalar_one()
            version = None
            try:
                version = (await conn.execute(text("select version_num from alembic_version"))).scalar_one()
            except Exception:  # noqa: BLE001
                version = None
            logger.info(
                "Database schema check | public_tables={} | alembic_version={}",
                count,
                version,
            )

        logger.info("Applying alembic upgrade head")
        try:
            await asyncio.to_thread(_run_alembic_upgrade)
        except Exception:
            logger.exception("Alembic upgrade head failed")
            if int(count) == 0:
                logger.warning("Falling back to SQLAlchemy metadata.create_all()")
                await _create_all_tables(engine)

        async with engine.connect() as conn2:
            after = (
                await conn2.execute(
                    text(
                        "select count(*) from information_schema.tables "
                        "where table_schema='public' and table_type='BASE TABLE'"
                    )
                )
            ).scalar_one()
            version_after = None
            try:
                version_after = (
                    await conn2.execute(text("select version_num from alembic_version"))
                ).scalar_one()
            except Exception:  # noqa: BLE001
                version_after = None
        logger.info(
            "Database schema ready | public_tables={} | alembic_version={}",
            after,
            version_after,
        )
        if int(after) == 0:
            msg = "Database still has zero public tables after schema bootstrap"
            logger.error(msg)
            raise RuntimeError(msg)
    finally:
        await engine.dispose()


async def ensure_chef_account(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Redis,
    settings: Settings,
) -> None:
    """Ensure the kitchen chef account exists in PostgreSQL + user.json."""
    try:
        async with session_factory() as session:
            auth = AuthService(
                session=session,
                settings=settings,
                redis_auth=RedisAuthRepository(redis, settings),
                jwt_service=JWTService(settings),
                user_sync=UserSyncService(),
                email_service=None,
            )
            chef = await auth.ensure_chef_account()
            logger.info(
                "Chef bootstrap complete | user_id={} | email={}",
                chef.id,
                chef.email,
            )
    except Exception:
        logger.exception("Chef account bootstrap failed — kitchen login may be unavailable")


async def ensure_demo_catalog(
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Seed a minimal visible menu when categories are empty."""
    try:
        async with session_factory() as session:
            cat_count = (
                await session.execute(select(func.count()).select_from(Category))
            ).scalar_one()
            if cat_count > 0:
                logger.info("Demo catalog seed skipped | categories={}", cat_count)
                return

            demos = [
                ("Pizzas", "Hand-tossed pizzas fresh from the oven", 1),
                ("Sides", "Garlic bread and extras", 2),
                ("Drinks", "Chilled beverages", 3),
            ]
            created: list[Category] = []
            for name, desc, order in demos:
                cat = Category(
                    name=name,
                    slug=slugify(name),
                    description=desc,
                    display_order=order,
                    is_visible=True,
                )
                session.add(cat)
                created.append(cat)
            await session.flush()

            products = [
                ("Margherita", created[0], "1500.00", "Tomato, mozzarella, basil"),
                ("Pepperoni Feast", created[0], "1899.00", "Loaded pepperoni pizza"),
                ("Garlic Bread", created[1], "499.00", "Buttery garlic bread"),
                ("Cola 1.5L", created[2], "250.00", "Chilled soft drink"),
            ]
            for name, cat, price, desc in products:
                session.add(
                    Product(
                        category_id=cat.id,
                        name=name,
                        slug=slugify(name),
                        description=desc,
                        short_description=desc,
                        base_price=Decimal(price),
                        is_available=True,
                        is_visible=True,
                        is_featured=True,
                        stock_status=StockStatus.IN_STOCK,
                        tags=["demo"],
                    )
                )
            await session.commit()
            logger.info(
                "Demo catalog seeded | categories={} | products={}",
                len(demos),
                len(products),
            )
    except Exception:
        logger.exception("Demo catalog seed failed")


async def ensure_demo_coupons(
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Idempotently seed storefront demo coupons (e.g. Apple20 = 30% off)."""
    demos = [
        ("APPLE20", "30% off with Apple20", CouponType.PERCENTAGE, Decimal("30.00")),
        ("PRIME10", "10% off", CouponType.PERCENTAGE, Decimal("10.00")),
        ("WELCOME5", "Fixed Rs 5 off", CouponType.FIXED, Decimal("5.00")),
    ]
    try:
        async with session_factory() as session:
            created = 0
            for code, description, coupon_type, value in demos:
                existing = (
                    await session.execute(
                        select(Coupon).where(
                            Coupon.code == code,
                            Coupon.deleted_at.is_(None),
                        )
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    continue
                session.add(
                    Coupon(
                        code=code,
                        description=description,
                        coupon_type=coupon_type,
                        value=value,
                        is_active=True,
                    )
                )
                created += 1
            if created:
                await session.commit()
            logger.info("Demo coupons seed complete | created={}", created)
    except Exception:
        logger.exception("Demo coupons seed failed")
