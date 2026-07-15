"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    account_aliases,
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
    contact,
    health,
    kitchen,
    orders,
    users,
    wishlist,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(contact.router)
api_v1_router.include_router(account_aliases.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(catalog.router)
api_v1_router.include_router(admin_catalog.router)
api_v1_router.include_router(cart.router)
api_v1_router.include_router(wishlist.router)
api_v1_router.include_router(checkout.router)
# Chef kitchen aliases must be registered before /orders/{order_id} catch-all.
api_v1_router.include_router(kitchen.router)
api_v1_router.include_router(kitchen.chef_router)
api_v1_router.include_router(kitchen.orders_kitchen_router)
api_v1_router.include_router(kitchen.dashboard_chef_router)
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
