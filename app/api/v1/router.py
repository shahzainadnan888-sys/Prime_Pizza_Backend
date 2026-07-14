"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_audit,
    admin_catalog,
    admin_coupons,
    admin_customers,
    admin_dashboard,
    admin_email,
    admin_notifications,
    admin_orders,
    admin_search,
    admin_settings,
    auth,
    cart,
    catalog,
    checkout,
    health,
    orders,
    users,
    wishlist,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(catalog.router)
api_v1_router.include_router(admin_catalog.router)
api_v1_router.include_router(cart.router)
api_v1_router.include_router(wishlist.router)
api_v1_router.include_router(checkout.router)
api_v1_router.include_router(orders.router)
api_v1_router.include_router(admin_orders.router)
api_v1_router.include_router(admin_email.router)
api_v1_router.include_router(admin_dashboard.router)
api_v1_router.include_router(admin_customers.router)
api_v1_router.include_router(admin_coupons.router)
api_v1_router.include_router(admin_notifications.router)
api_v1_router.include_router(admin_settings.router)
api_v1_router.include_router(admin_audit.router)
api_v1_router.include_router(admin_search.router)

# Health-only router for root-level probes (no auth exposure at /auth)
health_router = APIRouter()
health_router.include_router(health.router)
