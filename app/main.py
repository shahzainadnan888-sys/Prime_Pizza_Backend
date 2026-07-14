"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.api.router import register_routers
from app.common.constants import AppConstants
from app.config.settings import Settings, get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.middleware.registration import register_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Application factory.

    Builds a fully configured FastAPI instance with lifespan, middleware,
    routers, and exception handlers — without binding global side effects
    until the app is actually created.
    """
    resolved = settings or get_settings()
    setup_logging(resolved)

    docs_url = "/docs" if resolved.docs_enabled else None
    redoc_url = "/redoc" if resolved.docs_enabled else None
    openapi_url = "/openapi.json" if resolved.docs_enabled else None

    app = FastAPI(
        title=AppConstants.API_TITLE,
        version=__version__,
        description=AppConstants.API_DESCRIPTION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
        contact={
            "name": "Prime Pizza Engineering",
            "email": str(resolved.owner_email),
        },
        license_info={"name": "Proprietary"},
        openapi_tags=[
            {"name": "Health", "description": "Liveness and readiness probes"},
            {"name": "Authentication", "description": "Phone OTP authentication (local Redis OTP + JWT)"},
            {"name": "Users", "description": "Profile, addresses, preferences, and notifications"},
            {"name": "Catalog", "description": "Public categories, products, search, and deals"},
            {"name": "Admin Catalog", "description": "Owner-only menu management"},
            {"name": "Cart", "description": "Shopping cart and coupon preparation"},
            {"name": "Wishlist", "description": "Customer wishlist"},
            {"name": "Checkout", "description": "Checkout validation (no order creation)"},
            {"name": "Orders", "description": "Customer order placement, history, and tracking"},
            {"name": "Admin Orders", "description": "Owner order management"},
            {"name": "Admin Email", "description": "Owner transactional email testing"},
            {"name": "Admin Dashboard", "description": "Owner dashboard stats, analytics, and charts"},
            {"name": "Admin Customers", "description": "Owner customer list and profile management"},
            {"name": "Admin Coupons", "description": "Owner coupon CRUD and usage reports"},
            {"name": "Admin Notifications", "description": "Owner notification create and broadcast"},
            {"name": "Admin Settings", "description": "Restaurant and system settings"},
            {"name": "Admin Audit", "description": "Owner audit log browsing"},
            {"name": "Admin Search", "description": "Owner console multi-entity search"},
        ],
    )

    app.state.settings = resolved

    register_middleware(app, resolved)
    register_exception_handlers(app)
    register_routers(app, resolved)

    return app


# ASGI entrypoint for uvicorn: `uvicorn app.main:app`
app = create_app()
