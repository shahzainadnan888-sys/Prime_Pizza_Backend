# Database Architecture

## Tables (25)

Users, Addresses, Categories, Products, Product Images, Product Variants,
Variant Options, Product Options, Deals, Deal Products, Carts, Cart Items,
Cart Item Extras, Wishlists, Wishlist Items, Orders, Order Items,
Order Item Extras, Coupons, Coupon Usages, Notifications,
Notification Preferences, OTP Logs, Audit Logs, System Settings.

## Base model

Every entity inherits `BaseModel`:
UUID PK, `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`, `version`.

## Migration

```bash
alembic upgrade head
# revision: ed72b3fc94e8_create_prime_pizza_schema
```

## JSON mirror

`data/users.json` + `app.data_mirror.users.UsersJsonMirror` (dual-write deferred).
