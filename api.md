# Prime Pizza API — Frontend Source of Truth

> Generated from the **live** FastAPI OpenAPI schema for the current backend.
> Interactive docs: `{BASE_URL}/docs` · OpenAPI JSON: `{BASE_URL}/openapi.json`
>
> Do **not** invent endpoints. If it is not listed here, it is not part of this API.

**Generated operations in this file:** 132 canonical endpoints  
**Roles:** `customer` | `chef` only (there is **no** separate `admin` role; chef uses `/admin/*` with permissions)  
**Auth:** email + password → JWT Bearer (**no OTP / Twilio / Resend**)  
**Email provider:** Brevo (server-side only — API keys never leave the backend)

---

## Table of contents

1. [Base URL](#base-url)
2. [Response envelope](#response-envelope)
3. [Authentication & JWT](#authentication--jwt)
4. [Roles & permissions](#roles--permissions)
5. [Brevo emails](#brevo-emails)
6. [File uploads](#file-uploads)
7. [Order status values](#order-status-values)
8. [Pagination, filtering & sorting](#pagination-filtering--sorting)
9. [Environment & infrastructure](#environment--infrastructure)
10. [Global error responses](#global-error-responses)
11. [Frontend integration notes](#frontend-integration-notes)
12. [Endpoint catalog](#endpoint-catalog)
13. [Detailed endpoints](#detailed-endpoints)
14. [Integration summary](#integration-summary)

---

## Base URL

| Environment | Example |
|-------------|---------|
| Local | `http://127.0.0.1:8000` |
| Production | set by deployment |

All business routes: `{BASE_URL}/api/v1/...`

Health probes also exist without the `/api/v1` prefix (`/health`, `/health/database`, …).

---

## Response envelope

### Success

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "meta": null,
  "request_id": "uuid"
}
```

### Paginated success

`data` is an array. Paging metadata is in `meta`:

```json
{
  "success": true,
  "message": "Success",
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  },
  "request_id": "uuid"
}
```

### Error

```json
{
  "success": false,
  "message": "Human-readable message",
  "error": {
    "code": "validation_error",
    "details": []
  },
  "status_code": 422,
  "request_id": "uuid"
}
```

---

## Authentication & JWT

### Flows

| Action | Method & path | Auth | Notes |
|--------|---------------|------|-------|
| Register | `POST /api/v1/auth/register` | Public | Saves user to Neon + `data/user.json`; schedules Welcome email |
| Login | `POST /api/v1/auth/login` | Public | Returns JWT pair + `role` |
| Refresh | `POST /api/v1/auth/refresh` | Public (body has refresh token) | Rotates tokens |
| Logout | `POST /api/v1/auth/logout` | Bearer access token | Blacklists access token |
| Current user (auth) | `GET /api/v1/auth/me` | Bearer | Auth-centric me payload |
| Current profile | `GET /api/v1/users/me` | Bearer | Full profile |
| Profile alias | `GET /api/v1/account` | Bearer | Alias of `GET /users/me` |
| Profile update | `PATCH /api/v1/users/me` | Bearer | Partial profile update |
| Avatar upload | `POST /api/v1/users/avatar` | Bearer | `multipart/form-data` |
| Avatar delete | `DELETE /api/v1/users/avatar` | Bearer | |
| Password change | — | — | **Not implemented** in this backend |

### Register body (required)

| Field | Rules |
|-------|-------|
| `first_name`, `last_name` | 1–80 chars, non-empty after trim |
| `email` | valid email, stored lowercase |
| `password` | 8–128 chars; must include upper, lower, and digit |
| `confirm_password` | must match `password` |
| `phone_number` | optional; if set, E.164 (e.g. `+923001234567`) |

### Login body

| Field | Rules |
|-------|-------|
| `email` | required |
| `password` | required |

### Auth success `data` (register / login / refresh)

Flattened fields are included for frontend convenience:

- `access_token`, `refresh_token`, `token_type` (`bearer`), `expires_in` (seconds)
- `role` (`customer` | `chef`)
- `user` object (`id`, `first_name`, `last_name`, `email`, `phone_number`, `full_name`, `name`, `role`, `is_verified`, `is_active`, `created_at`)
- `tokens` nested pair (same tokens)
- `is_new_user` (register = true)

### Authorization header (all protected routes)

```http
Authorization: Bearer <access_token>
```

### JWT claims (access + refresh)

Issued claims include: `sub` / `user_id`, `email`, `phone_number`, `role`, `token_type` (`access`|`refresh`), `iat`, `exp`, `jti`.

**Authorization decisions use the database role**, not a forged JWT `role` claim.

### Protected routes

Any route marked “Bearer” below requires a valid, non-blacklisted access token. Unverified accounts may be rejected on verified-only routes.

---

## Roles & permissions

| Role | Purpose |
|------|---------|
| `customer` | Storefront: profile, cart, wishlist, checkout, own orders |
| `chef` | Kitchen dashboard + `/api/v1/admin/*` (chef permissions) |

There is **no** `admin` role string. Chef account is bootstrapped from env:

- Email: `CHEF_EMAIL`
- Password: `CHEF_PASSWORD`

Customers calling kitchen or `/admin/*` routes receive **403**.

### Public (no auth)

Health probes, register/login/refresh, public catalog (categories/products/deals GET), contact form.

### Customer endpoints (primary)

`/users/*`, `/account`, `/addresses`, `/cart/*`, `/wishlist/*`, `/checkout/*`, `/orders/*` (own orders).

### Chef endpoints

- Kitchen: `/api/v1/kitchen/*` (aliases: `/chef/*`, `/orders/kitchen/*`, `/dashboard/chef/*`)
- Owner console: `/api/v1/admin/*` (catalog, orders, customers, coupons, settings, notifications, audit, search, test-email)

---

## Brevo emails

Frontend **never** calls Brevo. The frontend only hits backend APIs; the backend `EmailService` sends via Brevo using server env vars. **Never put `BREVO_API_KEY` in frontend code or public env.**

| Trigger API | Email(s) | Delivery behavior |
|-------------|----------|-------------------|
| `POST /api/v1/auth/register` | **Welcome** → customer email | Best-effort after Neon + `user.json` save; registration **never fails** if email fails (logged) |
| `POST /api/v1/contact` | **Contact notification** → `CONTACT_RECEIVER_EMAIL` (+ admin inbox); optional customer confirmation | Admin inbox is **awaited**; Brevo failure → **HTTP 502** `brevo_service_error` |
| `POST /api/v1/orders` | **Order confirmation** → customer; **Chef notification** → `CHEF_EMAIL` | Scheduled after Neon + `order.json` save; place-order **HTTP success is not blocked** on Brevo |
| `POST /api/v1/admin/test-email` | Explicit connectivity test | Awaited; chef only; 502 on failure |

### Order confirmation content (customer)

Order number, customer name, line items (qty + prices), delivery address, payment method, order total, estimated delivery / prep time.

### Chef notification content

Customer name, phone, address, items, total, order ID / order number → inbox from `CHEF_EMAIL`.

### Related env names only (no values)

`BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `BREVO_SENDER_NAME`, `EMAIL_ENABLED`, `EMAIL_BRAND_NAME`, `EMAIL_LOGO_URL`, `ADMIN_EMAIL`, `CONTACT_RECEIVER_EMAIL`, `CHEF_EMAIL`, `OWNER_NOTIFICATION_EMAILS`

Startup **fails fast** when `EMAIL_ENABLED=true` and required Brevo vars are missing (skipped when `APP_ENV=test`).

---

## File uploads

| Endpoint | Auth | Multipart field | Max size (env) | Accepted types (env) |
|----------|------|-----------------|----------------|----------------------|
| `POST /api/v1/users/avatar` | Bearer | `file` | `AVATAR_MAX_BYTES` (default 5 MiB) | `AVATAR_ALLOWED_CONTENT_TYPES` — jpeg, png, webp, gif |
| `POST /api/v1/admin/products/{product_id}/images` | Bearer + chef | `file` (+ optional `alt_text`, `is_primary`) | `PRODUCT_IMAGE_MAX_BYTES` (default 5 MiB) | Image types validated server-side; max `MAX_PRODUCT_IMAGES` per product |

Uploaded assets are stored via **Cloudinary** (credentials server-side only).

---

## Order status values

Canonical enum:

`pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded`

### Kitchen vocabulary (boards / PATCH status)

| Kitchen term | Maps to |
|--------------|---------|
| `pending` / `incoming` | pending + confirmed board |
| `preparing` | preparing |
| `ready` | ready (+ out_for_delivery on board) |
| `completed` | delivered |
| `cancelled` | cancelled (+ refunded on board) |

Kitchen `PATCH .../status` accepts: `pending`, `preparing`, `ready`, `completed`, `cancelled` (aliases like `incoming` → pending).

---

## Pagination, filtering & sorting

### Pagination (when present)

| Param | Default | Constraints |
|-------|---------|-------------|
| `page` | `1` | ≥ 1 |
| `page_size` | `20` | 1–100 |

Used on: product lists/search, customer orders, admin orders/customers/coupons/audit, etc.

### Catalog filtering / search (examples)

`GET /api/v1/products` and `GET /api/v1/products/search` accept query params documented per endpoint (category, featured, search `q`, sort, etc.). See each endpoint’s **Query Parameters** table below.

### Cart quantity validation

Env-driven: `CART_MIN_ITEM_QUANTITY`, `CART_MAX_ITEM_QUANTITY`, `CART_MAX_ITEMS`.

---

## Environment & infrastructure

### Environment variables (names only — never commit values)

| Group | Variable names |
|-------|----------------|
| App | `APP_NAME`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX`, `HOST`, `PORT`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `ENABLE_DOCS`, `LOG_LEVEL` |
| Security | `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `TRUST_X_FORWARDED_FOR`, `TRUSTED_PROXY_IPS`, `ENABLE_HSTS`, `HSTS_MAX_AGE_SECONDS`, `ENABLE_CSP`, `CONTENT_SECURITY_POLICY`, `MAX_REQUEST_BODY_BYTES` |
| Neon / DB | `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE_SECONDS`, `DB_POOL_TIMEOUT_SECONDS` |
| Redis | `REDIS_URL`, `REDIS_MAX_CONNECTIONS` |
| Cloudinary | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` |
| Brevo | `BREVO_API_KEY`, `BREVO_SENDER_NAME`, `BREVO_SENDER_EMAIL`, `EMAIL_ENABLED`, `EMAIL_MAX_RETRIES`, `EMAIL_RETRY_BACKOFF_SECONDS`, `EMAIL_BRAND_NAME`, `EMAIL_LOGO_URL` |
| Inboxes | `ADMIN_EMAIL`, `CONTACT_RECEIVER_EMAIL`, `OWNER_EMAIL`, `OWNER_NOTIFICATION_EMAILS`, `CHEF_EMAIL`, `CHEF_PASSWORD`, `OWNER_PHONE_NUMBER` |
| Rate limits | `RATE_LIMIT_*`, `AUTH_*_LIMIT`, `AUTH_*_WINDOW_SECONDS` |
| Catalog / uploads | `AVATAR_MAX_BYTES`, `AVATAR_ALLOWED_CONTENT_TYPES`, `MAX_PRODUCT_IMAGES`, `PRODUCT_IMAGE_MAX_BYTES`, `CATALOG_CACHE_TTL_SECONDS` |
| Cart / orders | `CART_*`, `DELIVERY_FEE_FLAT`, `FREE_DELIVERY_THRESHOLD`, `TAX_RATE_PERCENT`, `ORDER_*`, `CHECKOUT_LOCK_TTL_SECONDS`, `ESTIMATED_*` |

### Required services

| Service | Purpose |
|---------|---------|
| **Neon PostgreSQL** | Primary system of record (users, orders, catalog, contact messages, email logs, …) |
| **Redis** (e.g. Upstash `rediss://`) | Auth rate limits, token blacklist, HTTP rate limiting, caches |
| **Brevo** | Transactional email (welcome, contact, order confirmation, chef notification) |
| **Cloudinary** | Avatar + product image storage |

### Local JSON mirrors (dual-write)

| File | Written when |
|------|----------------|
| `data/user.json` | After successful registration / user sync |
| `data/order.json` | After successful order placement / order sync |

These complement Neon; the API does **not** expose raw file contents as HTTP endpoints.

### CORS

Driven by `FRONTEND_URL`. In `APP_ENV=development`, local Vite/Next origins (`localhost:3000`, `5173`, `4173`, etc.) are also allowed. Production should set HTTPS `FRONTEND_URL` and proper `ALLOWED_HOSTS`.

---

## Global error responses

| HTTP | Typical `error.code` | When |
|------|----------------------|------|
| 400 | `app_error` / domain codes | Bad request |
| 401 | `unauthorized` / `invalid_token` / `expired_token` | Missing/invalid/expired/revoked token |
| 403 | `forbidden` | Authenticated but not allowed (e.g. customer → kitchen) |
| 404 | `not_found` | Missing resource |
| 409 | `conflict` | Duplicate email/phone, checkout lock, etc. |
| 422 | `validation_error` | Pydantic / business validation |
| 429 | `rate_limit` | Too many requests (`Retry-After` header) |
| 500 | `internal_error` | Unhandled server error |
| 502 | `brevo_service_error` | Contact admin email / admin test-email Brevo failure |
| 503 | `database_error` / `redis_error` / `rate_limit_unavailable` | Infrastructure |

### Example 401

```json
{
  "success": false,
  "message": "Authentication required",
  "error": { "code": "unauthorized", "details": null },
  "status_code": 401,
  "request_id": "..."
}
```

### Example 403

```json
{
  "success": false,
  "message": "Chef role required",
  "error": { "code": "forbidden", "details": null },
  "status_code": 403,
  "request_id": "..."
}
```

### Example 422

```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "validation_error",
    "details": [
      {
        "type": "missing",
        "loc": ["body", "confirm_password"],
        "msg": "Field required"
      }
    ]
  },
  "status_code": 422,
  "request_id": "..."
}
```

### Example 502 (contact form Brevo failure)

```json
{
  "success": false,
  "message": "Failed to send email via Brevo: …",
  "error": { "code": "brevo_service_error", "details": {} },
  "status_code": 502,
  "request_id": "..."
}
```

---

## Frontend integration notes

### Account aliases

| Frontend-friendly | Canonical |
|-------------------|-----------|
| `GET /api/v1/account` | `GET /api/v1/users/me` |
| `GET /api/v1/addresses` | `GET /api/v1/users/addresses` |
| `GET /api/v1/cart` | Active cart (stored totals; mutations recalculate) |

Always use the `/api/v1` prefix.

### Contact (frontend call)

```http
POST /api/v1/contact HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "name": "Sara Ahmed",
  "email": "sara@example.com",
  "phone": "+923001112233",
  "subject": "Catering",
  "message": "Do you cater for 50 guests?"
}
```

Aliases (same handler): `POST /api/v1/contact/`, `POST /api/v1/contacts`.

Success **201** — message saved and contact inbox email accepted by Brevo. On Brevo admin-send failure → **502**.

### Kitchen aliases (same handlers)

Prefer: `/api/v1/kitchen/*`

Also identical:

- `/api/v1/chef/*`
- `/api/v1/orders/kitchen/*`
- `/api/v1/dashboard/chef/*`

### Role routing after login

```ts
// data.role === "chef" → kitchen / admin UI
// data.role === "customer" → storefront
const token = data.access_token;
localStorage.setItem("access_token", token);
```

### Bearer example (profile)

```http
GET /api/v1/users/me HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
```

### Create order

`POST /api/v1/orders` with Bearer token. Default payment method: `cash_on_delivery`. Optional `Idempotency-Key` header / `idempotency_key` body field.

After success the backend dual-writes `data/order.json` and schedules customer confirmation + chef notification emails.

### Order GPS (checkout)

Optional live device coordinates on `POST /api/v1/orders`:

| Field | Required | Rules |
|-------|----------|-------|
| `latitude` | no | -90..90; must be sent with `longitude` |
| `longitude` | no | -180..180; must be sent with `latitude` |
| `gps_accuracy` | no | meters, >= 0; requires lat/lng |

Stored on the order row, echoed on `OrderDetailResponse` (`GET/POST /orders…`), kitchen cards, and mirrored into `data/order.json`. When omitted, lat/lng may fall back to the saved address coordinates; `gps_accuracy` stays null unless provided.

Example:

```json
{
  "address_id": "00000000-0000-4000-8000-000000000001",
  "payment_method": "cash_on_delivery",
  "latitude": 24.8607,
  "longitude": 67.0011,
  "gps_accuracy": 12.5
}
```

Response `data` includes the same three fields.

---

## Endpoint catalog

### Health

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/` | Public | API root |
| `GET` | `/api/v1/` | Public | API root |
| `GET` | `/api/v1/health` | Public | Liveness probe |
| `GET` | `/api/v1/health/database` | Public | Database readiness |
| `GET` | `/api/v1/health/redis` | Public | Redis readiness |
| `GET` | `/api/v1/health/services` | Public | Dependency and configuration readiness |
| `GET` | `/health` | Public | Liveness probe |
| `GET` | `/health/database` | Public | Database readiness |
| `GET` | `/health/redis` | Public | Redis readiness |
| `GET` | `/health/services` | Public | Dependency and configuration readiness |

### Authentication

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/auth/login` | Public | Login with email and password |
| `POST` | `/api/v1/auth/logout` | Bearer | Logout and revoke tokens |
| `GET` | `/api/v1/auth/me` | Bearer | Current authenticated user |
| `POST` | `/api/v1/auth/refresh` | Public | Refresh access token |
| `POST` | `/api/v1/auth/register` | Public | Register a customer account |

### Account

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/account` | Bearer | Get account profile (alias of /users/me) |
| `GET` | `/api/v1/addresses` | Bearer | List delivery addresses (alias of /users/addresses) |

### Users

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/users/addresses` | Bearer | List Addresses |
| `POST` | `/api/v1/users/addresses` | Bearer | Create Address |
| `DELETE` | `/api/v1/users/addresses/{address_id}` | Bearer | Delete Address |
| `PATCH` | `/api/v1/users/addresses/{address_id}` | Bearer | Update Address |
| `PATCH` | `/api/v1/users/addresses/{address_id}/default` | Bearer | Set Default Address |
| `DELETE` | `/api/v1/users/avatar` | Bearer | Delete Avatar |
| `POST` | `/api/v1/users/avatar` | Bearer | Upload Avatar |
| `DELETE` | `/api/v1/users/me` | Bearer | Soft Delete Account |
| `GET` | `/api/v1/users/me` | Bearer | Get My Profile |
| `PATCH` | `/api/v1/users/me` | Bearer | Update My Profile |
| `POST` | `/api/v1/users/me/deactivate` | Bearer | Deactivate Account |
| `GET` | `/api/v1/users/notifications` | Bearer | List Notifications |
| `PATCH` | `/api/v1/users/notifications/read-all` | Bearer | Mark All Notifications Read |
| `DELETE` | `/api/v1/users/notifications/{notification_id}` | Bearer | Delete Notification |
| `PATCH` | `/api/v1/users/notifications/{notification_id}/read` | Bearer | Mark Notification Read |
| `GET` | `/api/v1/users/preferences` | Bearer | Get Preferences |
| `PATCH` | `/api/v1/users/preferences` | Bearer | Update Preferences |

### Catalog

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/categories` | Public | List Categories |
| `GET` | `/api/v1/categories/{slug}` | Public | Get Category |
| `GET` | `/api/v1/deals` | Public | List Deals |
| `GET` | `/api/v1/deals/{slug}` | Public | Get Deal |
| `GET` | `/api/v1/products` | Public | List Products |
| `GET` | `/api/v1/products/featured` | Public | Featured Products |
| `GET` | `/api/v1/products/popular` | Public | Popular Products |
| `GET` | `/api/v1/products/recommended` | Public | Recommended Products |
| `GET` | `/api/v1/products/search` | Public | Search Products |
| `GET` | `/api/v1/products/{slug}` | Public | Get Product |

### Cart

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/cart` | Bearer | Get Cart |
| `POST` | `/api/v1/cart/apply-coupon` | Bearer | Apply Coupon |
| `DELETE` | `/api/v1/cart/clear` | Bearer | Clear Cart |
| `POST` | `/api/v1/cart/items` | Bearer | Add Cart Item |
| `DELETE` | `/api/v1/cart/items/{item_id}` | Bearer | Remove Cart Item |
| `PATCH` | `/api/v1/cart/items/{item_id}` | Bearer | Update Cart Item |
| `DELETE` | `/api/v1/cart/remove-coupon` | Bearer | Remove Coupon |
| `GET` | `/api/v1/cart/summary` | Bearer | Get Cart Summary |

### Wishlist

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/wishlist` | Bearer | Get Wishlist |
| `POST` | `/api/v1/wishlist` | Bearer | Add Wishlist Item |
| `DELETE` | `/api/v1/wishlist/clear` | Bearer | Clear Wishlist |
| `DELETE` | `/api/v1/wishlist/{product_id}` | Bearer | Remove Wishlist Item |

### Checkout

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/checkout/validate` | Bearer | Validate Checkout |

### Orders

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/orders` | Bearer | List My Orders |
| `POST` | `/api/v1/orders` | Bearer | Place Order |
| `GET` | `/api/v1/orders/{order_id}` | Bearer | Get My Order |
| `PATCH` | `/api/v1/orders/{order_id}/cancel` | Bearer | Cancel My Order |
| `GET` | `/api/v1/orders/{order_id}/tracking` | Bearer | Track My Order |

### Contact

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/contact` | Public | Submit contact form |

### Kitchen Dashboard

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/kitchen/orders` | Bearer | Kitchen order boards |
| `GET` | `/api/v1/kitchen/orders/cancelled` | Bearer | Cancelled kitchen orders |
| `GET` | `/api/v1/kitchen/orders/completed` | Bearer | Completed kitchen orders |
| `GET` | `/api/v1/kitchen/orders/incoming` | Bearer | Incoming kitchen orders |
| `GET` | `/api/v1/kitchen/orders/pending` | Bearer | Pending kitchen orders |
| `GET` | `/api/v1/kitchen/orders/preparing` | Bearer | Preparing kitchen orders |
| `GET` | `/api/v1/kitchen/orders/ready` | Bearer | Ready kitchen orders |
| `GET` | `/api/v1/kitchen/orders/{order_id}` | Bearer | Kitchen order details |
| `POST` | `/api/v1/kitchen/orders/{order_id}/accept` | Bearer | Accept incoming order |
| `POST` | `/api/v1/kitchen/orders/{order_id}/cancel` | Bearer | Cancel order |
| `POST` | `/api/v1/kitchen/orders/{order_id}/complete` | Bearer | Complete order |
| `POST` | `/api/v1/kitchen/orders/{order_id}/mark-ready` | Bearer | Mark order ready |
| `POST` | `/api/v1/kitchen/orders/{order_id}/start-preparing` | Bearer | Start preparing order |
| `PATCH` | `/api/v1/kitchen/orders/{order_id}/status` | Bearer | Update kitchen order status |

### Admin Email

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/admin/test-email` | Bearer | Send Test Email |

### Admin Dashboard

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/analytics` | Bearer | Get Analytics |
| `GET` | `/api/v1/admin/charts` | Bearer | Get Charts |
| `GET` | `/api/v1/admin/dashboard` | Bearer | Get Dashboard |

### Admin Orders

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/orders` | Bearer | List Orders |
| `GET` | `/api/v1/admin/orders/{order_id}` | Bearer | Get Order |
| `PATCH` | `/api/v1/admin/orders/{order_id}/notes` | Bearer | Update Order Notes |
| `PATCH` | `/api/v1/admin/orders/{order_id}/payment` | Bearer | Update Payment Status |
| `PATCH` | `/api/v1/admin/orders/{order_id}/status` | Bearer | Update Order Status |

### Admin Customers

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/customers` | Bearer | List Customers |
| `GET` | `/api/v1/admin/customers/{customer_id}` | Bearer | Get Customer |
| `PATCH` | `/api/v1/admin/customers/{customer_id}` | Bearer | Update Customer |
| `PATCH` | `/api/v1/admin/customers/{customer_id}/status` | Bearer | Update Customer Status |

### Admin Catalog

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/categories` | Bearer | List Admin Categories |
| `POST` | `/api/v1/admin/categories` | Bearer | Create Category |
| `PATCH` | `/api/v1/admin/categories/reorder` | Bearer | Reorder Categories |
| `DELETE` | `/api/v1/admin/categories/{category_id}` | Bearer | Delete Category |
| `PATCH` | `/api/v1/admin/categories/{category_id}` | Bearer | Update Category |
| `PATCH` | `/api/v1/admin/categories/{category_id}/hide` | Bearer | Hide Category |
| `PATCH` | `/api/v1/admin/categories/{category_id}/restore` | Bearer | Restore Category |
| `POST` | `/api/v1/admin/deals` | Bearer | Create Deal |
| `DELETE` | `/api/v1/admin/deals/{deal_id}` | Bearer | Delete Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}` | Bearer | Update Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/activate` | Bearer | Activate Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/deactivate` | Bearer | Deactivate Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/schedule` | Bearer | Schedule Deal |
| `POST` | `/api/v1/admin/products` | Bearer | Create Product |
| `POST` | `/api/v1/admin/products/bulk/availability` | Bearer | Bulk Product Availability |
| `POST` | `/api/v1/admin/products/bulk/category` | Bearer | Bulk Product Category |
| `POST` | `/api/v1/admin/products/bulk/delete` | Bearer | Bulk Product Delete |
| `POST` | `/api/v1/admin/products/bulk/featured` | Bearer | Bulk Product Featured |
| `POST` | `/api/v1/admin/products/bulk/visibility` | Bearer | Bulk Product Visibility |
| `DELETE` | `/api/v1/admin/products/{product_id}` | Bearer | Delete Product |
| `PATCH` | `/api/v1/admin/products/{product_id}` | Bearer | Update Product |
| `POST` | `/api/v1/admin/products/{product_id}/images` | Bearer | Upload Product Image |
| `PATCH` | `/api/v1/admin/products/{product_id}/images/reorder` | Bearer | Reorder Product Images |
| `DELETE` | `/api/v1/admin/products/{product_id}/images/{image_id}` | Bearer | Delete Product Image |

### Admin Coupons

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/coupons` | Bearer | List Coupons |
| `POST` | `/api/v1/admin/coupons` | Bearer | Create Coupon |
| `DELETE` | `/api/v1/admin/coupons/{coupon_id}` | Bearer | Delete Coupon |
| `GET` | `/api/v1/admin/coupons/{coupon_id}` | Bearer | Get Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}` | Bearer | Update Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}/disable` | Bearer | Disable Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}/enable` | Bearer | Enable Coupon |
| `GET` | `/api/v1/admin/coupons/{coupon_id}/usage` | Bearer | Get Coupon Usage |

### Admin Notifications

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/admin/notifications` | Bearer | Create Notification |
| `POST` | `/api/v1/admin/notifications/broadcast` | Bearer | Broadcast Notification |
| `DELETE` | `/api/v1/admin/notifications/{notification_id}` | Bearer | Delete Notification |

### Admin Settings

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/settings` | Bearer | List Settings |
| `PUT` | `/api/v1/admin/settings` | Bearer | Bulk Update Settings |
| `GET` | `/api/v1/admin/settings/restaurant` | Bearer | Get Restaurant Settings |
| `GET` | `/api/v1/admin/settings/{key}` | Bearer | Get Setting |
| `PUT` | `/api/v1/admin/settings/{key}` | Bearer | Upsert Setting |

### Admin Audit

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/api/v1/admin/audit-logs` | Bearer | List Audit Logs |

### Admin Search

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `POST` | `/api/v1/admin/search` | Bearer | Admin Search |


### Kitchen URL aliases (not repeated below)

Same operations as `/api/v1/kitchen/*` are also mounted at:

`/api/v1/chef/*`, `/api/v1/orders/kitchen/*`, `/api/v1/dashboard/chef/*`

---

## Detailed endpoints

## API root

### Endpoint

`GET /`

### Description

Service identity endpoint.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## API root

### Endpoint

`GET /api/v1/`

### Description

Service identity endpoint.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Liveness probe

### Endpoint

`GET /api/v1/health`

### Description

Process liveness — does not check external dependencies.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Database readiness

### Endpoint

`GET /api/v1/health/database`

### Description

Verify PostgreSQL connectivity.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Redis readiness

### Endpoint

`GET /api/v1/health/redis`

### Description

Verify Redis connectivity.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Dependency and configuration readiness

### Endpoint

`GET /api/v1/health/services`

### Description

Aggregate readiness for database, Redis, and configured third-party services.

Cloudinary / Brevo checks verify configuration presence (not live
outbound calls) to avoid costing API credits on every probe.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Liveness probe

### Endpoint

`GET /health`

### Description

Process liveness — does not check external dependencies.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Database readiness

### Endpoint

`GET /health/database`

### Description

Verify PostgreSQL connectivity.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Redis readiness

### Endpoint

`GET /health/redis`

### Description

Verify Redis connectivity.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Dependency and configuration readiness

### Endpoint

`GET /health/services`

### Description

Aggregate readiness for database, Redis, and configured third-party services.

Cloudinary / Brevo checks verify configuration presence (not live
outbound calls) to avoid costing API credits on every probe.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "request_id": "00000000-0000-4000-8000-000000000099"
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `503` | Service Unavailable |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Login with email and password

### Endpoint

`POST /api/v1/auth/login`

### Description

Validates credentials and issues a JWT access + refresh pair.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string (email) | yes | — |
| `password` | string | yes | minLength=1; maxLength=128 |

### Example Request

```http
POST /api/v1/auth/login HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "string"
}
```

### Validation Rules

- Required body fields: `email`, `password`
- `password`: minLength=1, maxLength=128

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Authenticated |
| `401` | Invalid credentials |
| `422` | Validation Error |
| `429` | Rate limited |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Logout and revoke tokens

### Endpoint

`POST /api/v1/auth/logout`

### Description

Logout and revoke tokens

### Authentication Required

Yes — Bearer access token

### Required Role

`customer` | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Current authenticated user

### Endpoint

`GET /api/v1/auth/me`

### Description

Current authenticated user

### Authentication Required

Yes — Bearer access token

### Required Role

`customer` | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Refresh access token

### Endpoint

`POST /api/v1/auth/refresh`

### Description

Refresh access token

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `refresh_token` | string | yes | minLength=20 |

### Example Request

```http
POST /api/v1/auth/refresh HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "refresh_token": "string"
}
```

### Validation Rules

- Required body fields: `refresh_token`
- `refresh_token`: minLength=20

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Register a customer account

### Endpoint

`POST /api/v1/auth/register`

### Description

Creates a customer with email/password (bcrypt), persists to PostgreSQL, mirrors to data/users.json, and returns a JWT access + refresh pair.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `first_name` | string | yes | minLength=1; maxLength=80 |
| `last_name` | string | yes | minLength=1; maxLength=80 |
| `email` | string (email) | yes | — |
| `password` | string | yes | minLength=8; maxLength=128 |
| `confirm_password` | string | yes | minLength=8; maxLength=128 |
| `phone_number` | string | null | no | — |

### Example Request

```http
POST /api/v1/auth/register HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "password": "string",
  "last_name": "string",
  "confirm_password": "string",
  "email": "user@example.com",
  "first_name": "string",
  "phone_number": null
}
```

### Validation Rules

- Required body fields: `confirm_password`, `email`, `first_name`, `last_name`, `password`
- `first_name`: minLength=1, maxLength=80
- `last_name`: minLength=1, maxLength=80
- `password`: minLength=8, maxLength=128
- `confirm_password`: minLength=8, maxLength=128

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Registered — returns token pair and user profile |
| `409` | Email or phone already registered |
| `422` | Validation error |
| `429` | Rate limited |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get account profile (alias of /users/me)

### Endpoint

`GET /api/v1/account`

### Description

Get account profile (alias of /users/me)

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List delivery addresses (alias of /users/addresses)

### Endpoint

`GET /api/v1/addresses`

### Description

List delivery addresses (alias of /users/addresses)

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Addresses

### Endpoint

`GET /api/v1/users/addresses`

### Description

List Addresses

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Address

### Endpoint

`POST /api/v1/users/addresses`

### Description

Create Address

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | minLength=1; maxLength=100 |
| `recipient_name` | string | yes | minLength=2; maxLength=150 |
| `phone_number` | string | yes | minLength=8; maxLength=20 |
| `street` | string | yes | minLength=3; maxLength=255 |
| `area` | string | null | no | — |
| `city` | string | yes | minLength=2; maxLength=100 |
| `province` | string | yes | minLength=2; maxLength=100 |
| `postal_code` | string | yes | minLength=3; maxLength=20 |
| `country` | string | no | minLength=2; maxLength=100; default=`"Pakistan"` |
| `latitude` | number | string | null | no | — |
| `longitude` | number | string | null | no | — |
| `delivery_notes` | string | null | no | — |
| `is_default` | boolean | no | default=`false` |

### Example Request

```http
POST /api/v1/users/addresses HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "city": "string",
  "province": "string",
  "street": "string",
  "title": "string",
  "phone_number": "string",
  "postal_code": "string",
  "recipient_name": "string",
  "area": null,
  "country": "Pakistan",
  "latitude": null,
  "longitude": null,
  "delivery_notes": null,
  "is_default": false
}
```

### Validation Rules

- Required body fields: `city`, `phone_number`, `postal_code`, `province`, `recipient_name`, `street`, `title`
- `title`: minLength=1, maxLength=100
- `recipient_name`: minLength=2, maxLength=150
- `phone_number`: minLength=8, maxLength=20
- `street`: minLength=3, maxLength=255
- `city`: minLength=2, maxLength=100
- `province`: minLength=2, maxLength=100
- `postal_code`: minLength=3, maxLength=20
- `country`: minLength=2, maxLength=100

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Address

### Endpoint

`DELETE /api/v1/users/addresses/{address_id}`

### Description

Delete Address

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `address_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Address

### Endpoint

`PATCH /api/v1/users/addresses/{address_id}`

### Description

Update Address

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `address_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | null | no | — |
| `recipient_name` | string | null | no | — |
| `phone_number` | string | null | no | — |
| `street` | string | null | no | — |
| `area` | string | null | no | — |
| `city` | string | null | no | — |
| `province` | string | null | no | — |
| `postal_code` | string | null | no | — |
| `country` | string | null | no | — |
| `latitude` | number | string | null | no | — |
| `longitude` | number | string | null | no | — |
| `delivery_notes` | string | null | no | — |
| `is_default` | boolean | null | no | — |

### Example Request

```http
PATCH /api/v1/users/addresses/{address_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": null,
  "recipient_name": null,
  "phone_number": null,
  "street": null,
  "area": null,
  "city": null,
  "province": null,
  "postal_code": null,
  "country": null,
  "latitude": null,
  "longitude": null,
  "delivery_notes": null,
  "is_default": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Set Default Address

### Endpoint

`PATCH /api/v1/users/addresses/{address_id}/default`

### Description

Set Default Address

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `address_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Avatar

### Endpoint

`DELETE /api/v1/users/avatar`

### Description

Delete Avatar

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Upload Avatar

### Endpoint

`POST /api/v1/users/avatar`

### Description

Upload Avatar

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: multipart/form-data` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | string | yes | — |

### Example Request

```http
POST /api/v1/users/avatar HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

(multipart form fields — see Request Body Schema)
```

### Validation Rules

- Required body fields: `file`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Soft Delete Account

### Endpoint

`DELETE /api/v1/users/me`

### Description

Soft Delete Account

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get My Profile

### Endpoint

`GET /api/v1/users/me`

### Description

Get My Profile

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update My Profile

### Endpoint

`PATCH /api/v1/users/me`

### Description

Update My Profile

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `full_name` | string | null | no | — |
| `email` | string (email) | null | no | — |

### Example Request

```http
PATCH /api/v1/users/me HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": null,
  "email": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Deactivate Account

### Endpoint

`POST /api/v1/users/me/deactivate`

### Description

Deactivate Account

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Notifications

### Endpoint

`GET /api/v1/users/notifications`

### Description

List Notifications

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Mark All Notifications Read

### Endpoint

`PATCH /api/v1/users/notifications/read-all`

### Description

Mark All Notifications Read

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Notification

### Endpoint

`DELETE /api/v1/users/notifications/{notification_id}`

### Description

Delete Notification

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `notification_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Mark Notification Read

### Endpoint

`PATCH /api/v1/users/notifications/{notification_id}/read`

### Description

Mark Notification Read

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `notification_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Preferences

### Endpoint

`GET /api/v1/users/preferences`

### Description

Get Preferences

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Preferences

### Endpoint

`PATCH /api/v1/users/preferences`

### Description

Update Preferences

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `dark_mode` | boolean | null | no | — |
| `language` | string | null | no | — |
| `marketing_emails` | boolean | null | no | — |
| `marketing_sms` | boolean | null | no | — |
| `push_notifications` | boolean | null | no | — |
| `order_updates` | boolean | null | no | — |
| `promotional_notifications` | boolean | null | no | — |
| `preferred_currency` | string | null | no | — |
| `preferred_timezone` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/users/preferences HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "dark_mode": null,
  "language": null,
  "marketing_emails": null,
  "marketing_sms": null,
  "push_notifications": null,
  "order_updates": null,
  "promotional_notifications": null,
  "preferred_currency": null,
  "preferred_timezone": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Categories

### Endpoint

`GET /api/v1/categories`

### Description

List Categories

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Category

### Endpoint

`GET /api/v1/categories/{slug}`

### Description

Get Category

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Deals

### Endpoint

`GET /api/v1/deals`

### Description

List Deals

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Deal

### Endpoint

`GET /api/v1/deals/{slug}`

### Description

Get Deal

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Products

### Endpoint

`GET /api/v1/products`

### Description

List Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category` | no | string | null | — |
| `category_id` | no | string (uuid) | null | — |
| `min_price` | no | number | string | null | — |
| `max_price` | no | number | string | null | — |
| `is_available` | no | boolean | null | — |
| `is_featured` | no | boolean | null | — |
| `is_popular` | no | boolean | null | — |
| `is_best_seller` | no | boolean | null | — |
| `vegetarian` | no | boolean | null | — |
| `tag` | no | enum: `popular` | `featured` | `new` | `limited` | `spicy` | `vegetarian` | `best_seller` | `chef_special` | `kids_favorite` | null | — |
| `min_calories` | no | integer | null | — |
| `max_calories` | no | integer | null | — |
| `max_preparation_time` | no | integer | null | — |
| `sort` | no | enum: `newest` | `oldest` | `price_asc` | `price_desc` | `popularity` | `alphabetical` | `preparation_time` | — |
| `q` | no | string | null | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "is_available": true,
      "sort_order": 1,
      "stock_status": "in_stock",
      "name": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "is_best_seller": true,
      "base_price": "string",
      "slug": "string",
      "is_popular": true,
      "category_id": "00000000-0000-4000-8000-000000000001",
      "is_featured": true,
      "short_description": null,
      "discount_price": null,
      "image_url": null,
      "preparation_time_minutes": null,
      "calories": null,
      "tags": [
        "string"
      ]
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Featured Products

### Endpoint

`GET /api/v1/products/featured`

### Description

Featured Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Popular Products

### Endpoint

`GET /api/v1/products/popular`

### Description

Popular Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Recommended Products

### Endpoint

`GET /api/v1/products/recommended`

### Description

Recommended Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_slug` | no | string | null | — |
| `category` | no | string | null | — |

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Search Products

### Endpoint

`GET /api/v1/products/search`

### Description

Search Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | yes | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "is_available": true,
      "sort_order": 1,
      "stock_status": "in_stock",
      "name": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "is_best_seller": true,
      "base_price": "string",
      "slug": "string",
      "is_popular": true,
      "category_id": "00000000-0000-4000-8000-000000000001",
      "is_featured": true,
      "short_description": null,
      "discount_price": null,
      "image_url": null,
      "preparation_time_minutes": null,
      "calories": null,
      "tags": [
        "string"
      ]
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Product

### Endpoint

`GET /api/v1/products/{slug}`

### Description

Get Product

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Cart

### Endpoint

`GET /api/v1/cart`

### Description

Get Cart

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Apply Coupon

### Endpoint

`POST /api/v1/cart/apply-coupon`

### Description

Apply Coupon

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | yes | minLength=2; maxLength=50 |

### Example Request

```http
POST /api/v1/cart/apply-coupon HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "code": "string"
}
```

### Validation Rules

- Required body fields: `code`
- `code`: minLength=2, maxLength=50

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Clear Cart

### Endpoint

`DELETE /api/v1/cart/clear`

### Description

Clear Cart

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Add Cart Item

### Endpoint

`POST /api/v1/cart/items`

### Description

Add Cart Item

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_id` | string (uuid) | yes | — |
| `variant_id` | string (uuid) | null | no | — |
| `quantity` | integer | no | min=1.0; max=100.0; default=`1` |
| `extra_option_ids` | array<string (uuid)> | no | — |
| `extras` | array<CartExtraInput> | no | — |
| `special_instructions` | string | null | no | — |

### Example Request

```http
POST /api/v1/cart/items HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": "00000000-0000-4000-8000-000000000001",
  "variant_id": null,
  "quantity": 1,
  "extra_option_ids": [
    "00000000-0000-4000-8000-000000000001"
  ],
  "extras": [
    {
      "option_id": "00000000-0000-4000-8000-000000000001",
      "quantity": 1
    }
  ],
  "special_instructions": null
}
```

### Validation Rules

- Required body fields: `product_id`
- `quantity`: min=1.0, max=100.0

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Remove Cart Item

### Endpoint

`DELETE /api/v1/cart/items/{item_id}`

### Description

Remove Cart Item

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `item_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Cart Item

### Endpoint

`PATCH /api/v1/cart/items/{item_id}`

### Description

Update Cart Item

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `item_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `quantity` | integer | null | no | — |
| `special_instructions` | string | null | no | — |
| `extra_option_ids` | array<string (uuid)> | null | no | — |
| `extras` | array<CartExtraInput> | null | no | — |

### Example Request

```http
PATCH /api/v1/cart/items/{item_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "quantity": null,
  "special_instructions": null,
  "extra_option_ids": null,
  "extras": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Remove Coupon

### Endpoint

`DELETE /api/v1/cart/remove-coupon`

### Description

Remove Coupon

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Cart Summary

### Endpoint

`GET /api/v1/cart/summary`

### Description

Get Cart Summary

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Wishlist

### Endpoint

`GET /api/v1/wishlist`

### Description

Get Wishlist

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Add Wishlist Item

### Endpoint

`POST /api/v1/wishlist`

### Description

Add Wishlist Item

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_id` | string (uuid) | yes | — |

### Example Request

```http
POST /api/v1/wishlist HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": "00000000-0000-4000-8000-000000000001"
}
```

### Validation Rules

- Required body fields: `product_id`

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Clear Wishlist

### Endpoint

`DELETE /api/v1/wishlist/clear`

### Description

Clear Wishlist

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Remove Wishlist Item

### Endpoint

`DELETE /api/v1/wishlist/{product_id}`

### Description

Remove Wishlist Item

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Validate Checkout

### Endpoint

`POST /api/v1/checkout/validate`

### Description

Validate Checkout

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List My Orders

### Endpoint

`GET /api/v1/orders`

### Description

List My Orders

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `status` | no | enum: `pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded` | null | — |
| `payment_status` | no | enum: `pending` | `paid` | `failed` | `refunded` | `partially_refunded` | `cancelled` | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "order_number": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "payment_method": "cash_on_delivery",
      "currency": "string",
      "updated_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "status": "pending",
      "grand_total": "string",
      "payment_status": "pending",
      "item_count": 0
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Place Order

### Endpoint

`POST /api/v1/orders`

### Description

Place Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |
| `Idempotency-Key` | recommended for `POST /orders` |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `address_id` | string (uuid) | null | no | — |
| `payment_method` | enum: `cash_on_delivery` | `card` | `online` | `wallet` | no | values: `cash_on_delivery`, `card`, `online`, `wallet` |
| `notes` | string | null | no | — |
| `idempotency_key` | string | null | no | — |
| `latitude` | number | string | null | no | — |
| `longitude` | number | string | null | no | — |
| `gps_accuracy` | number | string | null | no | GPS accuracy in meters, when reported by the device |

### Example Request

```http
POST /api/v1/orders HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "address_id": null,
  "payment_method": "cash_on_delivery",
  "notes": null,
  "idempotency_key": null,
  "latitude": null,
  "longitude": null,
  "gps_accuracy": null
}
```

### Validation Rules

- `payment_method`: enum=cash_on_delivery|card|online|wallet

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get My Order

### Endpoint

`GET /api/v1/orders/{order_id}`

### Description

Get My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Cancel My Order

### Endpoint

`PATCH /api/v1/orders/{order_id}/cancel`

### Description

Cancel My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Track My Order

### Endpoint

`GET /api/v1/orders/{order_id}/tracking`

### Description

Track My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Submit contact form

### Endpoint

`POST /api/v1/contact`

### Description

Stores the inquiry in PostgreSQL and emails CONTACT_RECEIVER_EMAIL via Brevo after commit. Required admin email failure returns HTTP 502.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | minLength=1; maxLength=150 |
| `email` | string (email) | yes | — |
| `phone` | string | null | no | — |
| `subject` | string | yes | minLength=1; maxLength=200 |
| `message` | string | yes | minLength=1; maxLength=5000 |

### Example Request

```http
POST /api/v1/contact HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "string",
  "message": "string",
  "subject": "string",
  "phone": null
}
```

### Validation Rules

- Required body fields: `email`, `message`, `name`, `subject`
- `name`: minLength=1, maxLength=150
- `subject`: minLength=1, maxLength=200
- `message`: minLength=1, maxLength=5000

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Kitchen order boards

### Endpoint

`GET /api/v1/kitchen/orders`

### Description

Returns pending/incoming, preparing, ready, completed, and cancelled orders for the chef kitchen dashboard.

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Cancelled kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/cancelled`

### Description

Cancelled kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Completed kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/completed`

### Description

Completed kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Incoming kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/incoming`

### Description

Incoming kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Pending kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/pending`

### Description

Pending kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Preparing kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/preparing`

### Description

Preparing kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Ready kitchen orders

### Endpoint

`GET /api/v1/kitchen/orders/ready`

### Description

Ready kitchen orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Kitchen order details

### Endpoint

`GET /api/v1/kitchen/orders/{order_id}`

### Description

Kitchen order details

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Accept incoming order

### Endpoint

`POST /api/v1/kitchen/orders/{order_id}/accept`

### Description

Accept incoming order

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Cancel order

### Endpoint

`POST /api/v1/kitchen/orders/{order_id}/cancel`

### Description

Cancel order

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Complete order

### Endpoint

`POST /api/v1/kitchen/orders/{order_id}/complete`

### Description

Complete order

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Mark order ready

### Endpoint

`POST /api/v1/kitchen/orders/{order_id}/mark-ready`

### Description

Mark order ready

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Start preparing order

### Endpoint

`POST /api/v1/kitchen/orders/{order_id}/start-preparing`

### Description

Start preparing order

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update kitchen order status

### Endpoint

`PATCH /api/v1/kitchen/orders/{order_id}/status`

### Description

Chef-only status updates: pending, preparing, ready, completed.

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (verified)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | string | yes | minLength=3; maxLength=32 |
| `notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/kitchen/orders/{order_id}/status HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "string",
  "notes": null
}
```

### Validation Rules

- Required body fields: `status`
- `status`: minLength=3, maxLength=32

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Send Test Email

### Endpoint

`POST /api/v1/admin/test-email`

### Description

Send Test Email

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No fields (or opaque object)._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Analytics

### Endpoint

`GET /api/v1/admin/analytics`

### Description

Get Analytics

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `period` | no | enum: `daily` | `weekly` | `monthly` | `yearly` | — |
| `limit` | no | integer | — |

### Request Body Schema

_No request body._

### Validation Rules

- `limit`: min=1, max=50

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Charts

### Endpoint

`GET /api/v1/admin/charts`

### Description

Get Charts

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `period` | no | enum: `daily` | `weekly` | `monthly` | `yearly` | — |

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Dashboard

### Endpoint

`GET /api/v1/admin/dashboard`

### Description

Get Dashboard

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Orders

### Endpoint

`GET /api/v1/admin/orders`

### Description

List Orders

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `status` | no | enum: `pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded` | null | — |
| `payment_status` | no | enum: `pending` | `paid` | `failed` | `refunded` | `partially_refunded` | `cancelled` | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `q` | no | string | null | — |
| `user_id` | no | string (uuid) | null | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "order_number": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "payment_method": "cash_on_delivery",
      "currency": "string",
      "updated_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "status": "pending",
      "grand_total": "string",
      "payment_status": "pending",
      "item_count": 0
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Order

### Endpoint

`GET /api/v1/admin/orders/{order_id}`

### Description

Get Order

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Order Notes

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/notes`

### Description

Update Order Notes

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `notes` | string | null | no | — |
| `kitchen_notes` | string | null | no | — |
| `internal_notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/notes HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "notes": null,
  "kitchen_notes": null,
  "internal_notes": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Payment Status

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/payment`

### Description

Update Payment Status

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `payment_status` | enum: `pending` | `paid` | `failed` | `refunded` | `partially_refunded` | `cancelled` | yes | values: `pending`, `paid`, `failed`, `refunded`, `partially_refunded`, `cancelled` |
| `notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/payment HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "payment_status": "pending",
  "notes": null
}
```

### Validation Rules

- Required body fields: `payment_status`
- `payment_status`: enum=pending|paid|failed|refunded|partially_refunded|cancelled

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Order Status

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/status`

### Description

Update Order Status

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum: `pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded` | yes | values: `pending`, `confirmed`, `preparing`, `ready`, `out_for_delivery`, `delivered`, `cancelled`, `refunded` |
| `notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/status HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "pending",
  "notes": null
}
```

### Validation Rules

- Required body fields: `status`
- `status`: enum=pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled|refunded

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Customers

### Endpoint

`GET /api/v1/admin/customers`

### Description

List Customers

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | no | string | null | — |
| `name` | no | string | null | — |
| `phone` | no | string | null | — |
| `email` | no | string | null | — |
| `role` | no | enum: `customer` | `chef` | null | — |
| `is_active` | no | boolean | null | — |
| `is_verified` | no | boolean | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "is_verified": true,
      "full_name": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "role": "customer",
      "is_active": true,
      "id": "00000000-0000-4000-8000-000000000001",
      "phone_number": "string",
      "email": null,
      "avatar_url": null,
      "last_login": null
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Customer

### Endpoint

`GET /api/v1/admin/customers/{customer_id}`

### Description

Get Customer

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `customer_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Customer

### Endpoint

`PATCH /api/v1/admin/customers/{customer_id}`

### Description

Update Customer

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `customer_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `full_name` | string | null | no | — |
| `email` | string (email) | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/customers/{customer_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": null,
  "email": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Customer Status

### Endpoint

`PATCH /api/v1/admin/customers/{customer_id}/status`

### Description

Update Customer Status

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `customer_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `is_active` | boolean | yes | — |

### Example Request

```http
PATCH /api/v1/admin/customers/{customer_id}/status HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_active": true
}
```

### Validation Rules

- Required body fields: `is_active`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Admin Categories

### Endpoint

`GET /api/v1/admin/categories`

### Description

List Admin Categories

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Category

### Endpoint

`POST /api/v1/admin/categories`

### Description

Create Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | minLength=2; maxLength=150 |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `image_url` | string | null | no | — |
| `display_order` | integer | no | min=0.0; default=`0` |
| `is_visible` | boolean | no | default=`true` |
| `seo_title` | string | null | no | — |
| `seo_description` | string | null | no | — |
| `seo_keywords` | string | null | no | — |

### Example Request

```http
POST /api/v1/admin/categories HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "slug": null,
  "description": null,
  "image_url": null,
  "display_order": 0,
  "is_visible": true,
  "seo_title": null,
  "seo_description": null,
  "seo_keywords": null
}
```

### Validation Rules

- Required body fields: `name`
- `name`: minLength=2, maxLength=150
- `display_order`: min=0.0

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Reorder Categories

### Endpoint

`PATCH /api/v1/admin/categories/reorder`

### Description

Reorder Categories

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `items` | array<CategoryReorderItem> | yes | — |

### Example Request

```http
PATCH /api/v1/admin/categories/reorder HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "items": [
    {
      "display_order": 1,
      "category_id": "00000000-0000-4000-8000-000000000001"
    }
  ]
}
```

### Validation Rules

- Required body fields: `items`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Category

### Endpoint

`DELETE /api/v1/admin/categories/{category_id}`

### Description

Delete Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Category

### Endpoint

`PATCH /api/v1/admin/categories/{category_id}`

### Description

Update Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | null | no | — |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `image_url` | string | null | no | — |
| `display_order` | integer | null | no | — |
| `is_visible` | boolean | null | no | — |
| `seo_title` | string | null | no | — |
| `seo_description` | string | null | no | — |
| `seo_keywords` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/categories/{category_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": null,
  "slug": null,
  "description": null,
  "image_url": null,
  "display_order": null,
  "is_visible": null,
  "seo_title": null,
  "seo_description": null,
  "seo_keywords": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Hide Category

### Endpoint

`PATCH /api/v1/admin/categories/{category_id}/hide`

### Description

Hide Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Restore Category

### Endpoint

`PATCH /api/v1/admin/categories/{category_id}/restore`

### Description

Restore Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Deal

### Endpoint

`POST /api/v1/admin/deals`

### Description

Create Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | minLength=2; maxLength=200 |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `deal_type` | enum: `combo` | `family` | `limited` | `time_based` | `weekend` | `festival` | yes | values: `combo`, `family`, `limited`, `time_based`, `weekend`, `festival` |
| `deal_price` | number | string | yes | — |
| `discount_percent` | number | string | null | no | — |
| `image_url` | string | null | no | — |
| `is_active` | boolean | no | default=`true` |
| `is_visible` | boolean | no | default=`true` |
| `starts_at` | string (date-time) | null | no | — |
| `ends_at` | string (date-time) | null | no | — |
| `products` | array<DealProductItem> | no | — |

### Example Request

```http
POST /api/v1/admin/deals HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "deal_price": null,
  "name": "string",
  "deal_type": "combo",
  "slug": null,
  "description": null,
  "discount_percent": null,
  "image_url": null,
  "is_active": true,
  "is_visible": true,
  "starts_at": null,
  "ends_at": null,
  "products": [
    {
      "product_id": "00000000-0000-4000-8000-000000000001",
      "quantity": 1
    }
  ]
}
```

### Validation Rules

- Required body fields: `deal_price`, `deal_type`, `name`
- `name`: minLength=2, maxLength=200
- `deal_type`: enum=combo|family|limited|time_based|weekend|festival

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Deal

### Endpoint

`DELETE /api/v1/admin/deals/{deal_id}`

### Description

Delete Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `deal_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Deal

### Endpoint

`PATCH /api/v1/admin/deals/{deal_id}`

### Description

Update Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `deal_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | null | no | — |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `deal_type` | enum: `combo` | `family` | `limited` | `time_based` | `weekend` | `festival` | null | no | — |
| `deal_price` | number | string | null | no | — |
| `discount_percent` | number | string | null | no | — |
| `image_url` | string | null | no | — |
| `is_active` | boolean | null | no | — |
| `is_visible` | boolean | null | no | — |
| `starts_at` | string (date-time) | null | no | — |
| `ends_at` | string (date-time) | null | no | — |
| `products` | array<DealProductItem> | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/deals/{deal_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": null,
  "slug": null,
  "description": null,
  "deal_type": null,
  "deal_price": null,
  "discount_percent": null,
  "image_url": null,
  "is_active": null,
  "is_visible": null,
  "starts_at": null,
  "ends_at": null,
  "products": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Activate Deal

### Endpoint

`PATCH /api/v1/admin/deals/{deal_id}/activate`

### Description

Activate Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `deal_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Deactivate Deal

### Endpoint

`PATCH /api/v1/admin/deals/{deal_id}/deactivate`

### Description

Deactivate Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `deal_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Schedule Deal

### Endpoint

`PATCH /api/v1/admin/deals/{deal_id}/schedule`

### Description

Schedule Deal

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `deal_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `starts_at` | string (date-time) | null | no | — |
| `ends_at` | string (date-time) | null | no | — |
| `is_active` | boolean | null | no | — |
| `is_visible` | boolean | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/deals/{deal_id}/schedule HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "starts_at": null,
  "ends_at": null,
  "is_active": null,
  "is_visible": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Product

### Endpoint

`POST /api/v1/admin/products`

### Description

Create Product

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `category_id` | string (uuid) | yes | — |
| `name` | string | yes | minLength=2; maxLength=200 |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `short_description` | string | null | no | — |
| `base_price` | number | string | yes | — |
| `discount_price` | number | string | null | no | — |
| `image_url` | string | null | no | — |
| `is_available` | boolean | no | default=`true` |
| `stock_status` | enum: `in_stock` | `out_of_stock` | `limited` | no | values: `in_stock`, `out_of_stock`, `limited` |
| `preparation_time_minutes` | integer | null | no | — |
| `calories` | integer | null | no | — |
| `is_featured` | boolean | no | default=`false` |
| `is_popular` | boolean | no | default=`false` |
| `is_best_seller` | boolean | no | default=`false` |
| `is_visible` | boolean | no | default=`true` |
| `sort_order` | integer | no | min=0.0; default=`0` |
| `tags` | array<enum: `popular` | `featured` | `new` | `limited` | `spicy` | `vegetarian` | `best_seller` | `chef_special` | `kids_favorite`> | no | — |
| `seo_title` | string | null | no | — |
| `seo_description` | string | null | no | — |
| `seo_keywords` | string | null | no | — |
| `variants` | array<VariantCreateRequest> | no | — |
| `extra_option_ids` | array<string (uuid)> | no | — |

### Example Request

```http
POST /api/v1/admin/products HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "category_id": "00000000-0000-4000-8000-000000000001",
  "base_price": null,
  "slug": null,
  "description": null,
  "short_description": null,
  "discount_price": null,
  "image_url": null,
  "is_available": true,
  "stock_status": "in_stock",
  "preparation_time_minutes": null,
  "calories": null,
  "is_featured": false,
  "is_popular": false,
  "is_best_seller": false,
  "is_visible": true,
  "sort_order": 0,
  "tags": [
    "popular"
  ],
  "seo_title": null,
  "seo_description": null,
  "seo_keywords": null,
  "variants": [
    {
      "price": null,
      "name": "string",
      "size": "small",
      "discount_price": null,
      "preparation_time_minutes": null,
      "is_available": true,
      "display_order": 0
    }
  ],
  "extra_option_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `base_price`, `category_id`, `name`
- `name`: minLength=2, maxLength=200
- `stock_status`: enum=in_stock|out_of_stock|limited
- `sort_order`: min=0.0

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Product Availability

### Endpoint

`POST /api/v1/admin/products/bulk/availability`

### Description

Bulk Product Availability

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_ids` | array<string (uuid)> | yes | — |
| `is_available` | boolean | yes | — |

### Example Request

```http
POST /api/v1/admin/products/bulk/availability HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_available": true,
  "product_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `is_available`, `product_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Product Category

### Endpoint

`POST /api/v1/admin/products/bulk/category`

### Description

Bulk Product Category

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_ids` | array<string (uuid)> | yes | — |
| `category_id` | string (uuid) | yes | — |

### Example Request

```http
POST /api/v1/admin/products/bulk/category HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "category_id": "00000000-0000-4000-8000-000000000001",
  "product_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `category_id`, `product_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Product Delete

### Endpoint

`POST /api/v1/admin/products/bulk/delete`

### Description

Bulk Product Delete

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_ids` | array<string (uuid)> | yes | — |

### Example Request

```http
POST /api/v1/admin/products/bulk/delete HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `product_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Product Featured

### Endpoint

`POST /api/v1/admin/products/bulk/featured`

### Description

Bulk Product Featured

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_ids` | array<string (uuid)> | yes | — |
| `is_featured` | boolean | yes | — |

### Example Request

```http
POST /api/v1/admin/products/bulk/featured HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_featured": true,
  "product_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `is_featured`, `product_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Product Visibility

### Endpoint

`POST /api/v1/admin/products/bulk/visibility`

### Description

Bulk Product Visibility

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_ids` | array<string (uuid)> | yes | — |
| `is_visible` | boolean | yes | — |

### Example Request

```http
POST /api/v1/admin/products/bulk/visibility HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_visible": true,
  "product_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `is_visible`, `product_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Product

### Endpoint

`DELETE /api/v1/admin/products/{product_id}`

### Description

Delete Product

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Product

### Endpoint

`PATCH /api/v1/admin/products/{product_id}`

### Description

Update Product

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `category_id` | string (uuid) | null | no | — |
| `name` | string | null | no | — |
| `slug` | string | null | no | — |
| `description` | string | null | no | — |
| `short_description` | string | null | no | — |
| `base_price` | number | string | null | no | — |
| `discount_price` | number | string | null | no | — |
| `image_url` | string | null | no | — |
| `is_available` | boolean | null | no | — |
| `stock_status` | enum: `in_stock` | `out_of_stock` | `limited` | null | no | — |
| `preparation_time_minutes` | integer | null | no | — |
| `calories` | integer | null | no | — |
| `is_featured` | boolean | null | no | — |
| `is_popular` | boolean | null | no | — |
| `is_best_seller` | boolean | null | no | — |
| `is_visible` | boolean | null | no | — |
| `sort_order` | integer | null | no | — |
| `tags` | array<enum: `popular` | `featured` | `new` | `limited` | `spicy` | `vegetarian` | `best_seller` | `chef_special` | `kids_favorite`> | null | no | — |
| `seo_title` | string | null | no | — |
| `seo_description` | string | null | no | — |
| `seo_keywords` | string | null | no | — |
| `variants` | array<VariantCreateRequest> | null | no | — |
| `extra_option_ids` | array<string (uuid)> | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/products/{product_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "category_id": null,
  "name": null,
  "slug": null,
  "description": null,
  "short_description": null,
  "base_price": null,
  "discount_price": null,
  "image_url": null,
  "is_available": null,
  "stock_status": null,
  "preparation_time_minutes": null,
  "calories": null,
  "is_featured": null,
  "is_popular": null,
  "is_best_seller": null,
  "is_visible": null,
  "sort_order": null,
  "tags": null,
  "seo_title": null,
  "seo_description": null,
  "seo_keywords": null,
  "variants": null,
  "extra_option_ids": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Upload Product Image

### Endpoint

`POST /api/v1/admin/products/{product_id}/images`

### Description

Upload Product Image

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: multipart/form-data` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | string | yes | — |
| `alt_text` | string | null | no | — |
| `is_primary` | boolean | no | default=`false` |

### Example Request

```http
POST /api/v1/admin/products/{product_id}/images HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

(multipart form fields — see Request Body Schema)
```

### Validation Rules

- Required body fields: `file`

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Reorder Product Images

### Endpoint

`PATCH /api/v1/admin/products/{product_id}/images/reorder`

### Description

Reorder Product Images

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `image_ids` | array<string (uuid)> | yes | — |

### Example Request

```http
PATCH /api/v1/admin/products/{product_id}/images/reorder HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "image_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

### Validation Rules

- Required body fields: `image_ids`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Product Image

### Endpoint

`DELETE /api/v1/admin/products/{product_id}/images/{image_id}`

### Description

Delete Product Image

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_id` | yes | string (uuid) | — |
| `image_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Coupons

### Endpoint

`GET /api/v1/admin/coupons`

### Description

List Coupons

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | no | string | null | — |
| `is_active` | no | boolean | null | — |
| `coupon_type` | no | enum: `percentage` | `fixed` | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "usage_limit": null,
      "created_at": "2026-07-15T12:00:00Z",
      "value": "string",
      "per_user_limit": null,
      "coupon_type": "percentage",
      "code": "string",
      "updated_at": "2026-07-15T12:00:00Z",
      "description": null,
      "is_active": true,
      "id": "00000000-0000-4000-8000-000000000001",
      "used_count": 1,
      "starts_at": null,
      "minimum_order_amount": null,
      "expires_at": null,
      "maximum_discount": null
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Coupon

### Endpoint

`POST /api/v1/admin/coupons`

### Description

Create Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | yes | minLength=3; maxLength=50 |
| `description` | string | null | no | — |
| `coupon_type` | enum: `percentage` | `fixed` | yes | values: `percentage`, `fixed` |
| `value` | number | string | yes | — |
| `minimum_order_amount` | number | string | null | no | — |
| `maximum_discount` | number | string | null | no | — |
| `usage_limit` | integer | null | no | — |
| `per_user_limit` | integer | null | no | — |
| `is_active` | boolean | no | default=`true` |
| `starts_at` | string (date-time) | null | no | — |
| `expires_at` | string (date-time) | null | no | — |

### Example Request

```http
POST /api/v1/admin/coupons HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "coupon_type": "percentage",
  "code": "string",
  "value": null,
  "description": null,
  "minimum_order_amount": null,
  "maximum_discount": null,
  "usage_limit": null,
  "per_user_limit": null,
  "is_active": true,
  "starts_at": null,
  "expires_at": null
}
```

### Validation Rules

- Required body fields: `code`, `coupon_type`, `value`
- `code`: minLength=3, maxLength=50
- `coupon_type`: enum=percentage|fixed

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Coupon

### Endpoint

`DELETE /api/v1/admin/coupons/{coupon_id}`

### Description

Delete Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Coupon

### Endpoint

`GET /api/v1/admin/coupons/{coupon_id}`

### Description

Get Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}`

### Description

Update Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | null | no | — |
| `coupon_type` | enum: `percentage` | `fixed` | null | no | — |
| `value` | number | string | null | no | — |
| `minimum_order_amount` | number | string | null | no | — |
| `maximum_discount` | number | string | null | no | — |
| `usage_limit` | integer | null | no | — |
| `per_user_limit` | integer | null | no | — |
| `is_active` | boolean | null | no | — |
| `starts_at` | string (date-time) | null | no | — |
| `expires_at` | string (date-time) | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/coupons/{coupon_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "description": null,
  "coupon_type": null,
  "value": null,
  "minimum_order_amount": null,
  "maximum_discount": null,
  "usage_limit": null,
  "per_user_limit": null,
  "is_active": null,
  "starts_at": null,
  "expires_at": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Disable Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}/disable`

### Description

Disable Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Enable Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}/enable`

### Description

Enable Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Coupon Usage

### Endpoint

`GET /api/v1/admin/coupons/{coupon_id}/usage`

### Description

Get Coupon Usage

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Notification

### Endpoint

`POST /api/v1/admin/notifications`

### Description

Create Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `user_id` | string (uuid) | null | no | — |
| `title` | string | yes | minLength=1; maxLength=200 |
| `message` | string | yes | minLength=1; maxLength=5000 |
| `notification_type` | enum: `order` | `promo` | `system` | `account` | no | values: `order`, `promo`, `system`, `account` |
| `payload` | object | null | no | — |
| `scheduled_at` | string (date-time) | null | no | Preparation only — stored in payload until a scheduler ships |

### Example Request

```http
POST /api/v1/admin/notifications HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "string",
  "title": "string",
  "user_id": null,
  "notification_type": "order",
  "payload": null,
  "scheduled_at": null
}
```

### Validation Rules

- Required body fields: `message`, `title`
- `title`: minLength=1, maxLength=200
- `message`: minLength=1, maxLength=5000
- `notification_type`: enum=order|promo|system|account

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Broadcast Notification

### Endpoint

`POST /api/v1/admin/notifications/broadcast`

### Description

Broadcast Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | yes | minLength=1; maxLength=200 |
| `message` | string | yes | minLength=1; maxLength=5000 |
| `notification_type` | enum: `order` | `promo` | `system` | `account` | no | values: `order`, `promo`, `system`, `account` |
| `payload` | object | null | no | — |
| `role_filter` | string | null | no | default=`"customer"` |
| `scheduled_at` | string (date-time) | null | no | — |

### Example Request

```http
POST /api/v1/admin/notifications/broadcast HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "string",
  "title": "string",
  "notification_type": "order",
  "payload": null,
  "role_filter": null,
  "scheduled_at": null
}
```

### Validation Rules

- Required body fields: `message`, `title`
- `title`: minLength=1, maxLength=200
- `message`: minLength=1, maxLength=5000
- `notification_type`: enum=order|promo|system|account

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Notification

### Endpoint

`DELETE /api/v1/admin/notifications/{notification_id}`

### Description

Delete Notification

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `notification_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Settings

### Endpoint

`GET /api/v1/admin/settings`

### Description

List Settings

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Bulk Update Settings

### Endpoint

`PUT /api/v1/admin/settings`

### Description

Bulk Update Settings

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `settings` | Settings | yes | — |

### Example Request

```http
PUT /api/v1/admin/settings HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "settings": {}
}
```

### Validation Rules

- Required body fields: `settings`

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Restaurant Settings

### Endpoint

`GET /api/v1/admin/settings/restaurant`

### Description

Get Restaurant Settings

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Setting

### Endpoint

`GET /api/v1/admin/settings/{key}`

### Description

Get Setting

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `key` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Upsert Setting

### Endpoint

`PUT /api/v1/admin/settings/{key}`

### Description

Upsert Setting

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `key` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `value` | string | null | no | — |
| `value_json` | object | array<any> | null | no | — |
| `description` | string | null | no | — |
| `is_public` | boolean | null | no | — |

### Example Request

```http
PUT /api/v1/admin/settings/{key} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "value": null,
  "value_json": null,
  "description": null,
  "is_public": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## List Audit Logs

### Endpoint

`GET /api/v1/admin/audit-logs`

### Description

List Audit Logs

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | no | string | null | — |
| `user_id` | no | string (uuid) | null | — |
| `action` | no | enum: `create` | `update` | `delete` | `login` | `logout` | `view` | `other` | null | — |
| `resource_type` | no | string | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "resource_type": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "user_id": null,
      "id": "00000000-0000-4000-8000-000000000001",
      "message": null,
      "user_agent": null,
      "resource_id": null,
      "ip_address": null,
      "details": null,
      "action": "create"
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Admin Search

### Endpoint

`POST /api/v1/admin/search`

### Description

Admin Search

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `q` | string | yes | minLength=1; maxLength=200 |
| `entities` | array<enum: `customers` | `orders` | `products` | `coupons` | `deals` | `categories` | `audit_logs`> | null | no | — |
| `limit_per_entity` | integer | no | min=1.0; max=50.0; default=`10` |

### Example Request

```http
POST /api/v1/admin/search HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "q": "string",
  "entities": null,
  "limit_per_entity": 10
}
```

### Validation Rules

- Required body fields: `q`
- `q`: minLength=1, maxLength=200
- `limit_per_entity`: min=1.0, max=50.0

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

---

## Integration summary

Counts below are **canonical** routes documented in this file (kitchen URL aliases are counted separately and are not duplicate handlers).

| Metric | Count |
|--------|------:|
| **Total canonical endpoints** | **132** |
| Public endpoints | 24 |
| Customer-primary endpoints | 39 |
| Chef-only endpoints (kitchen + `/admin/*`) | 69 |
| File upload endpoints | 2 |
| Email-related endpoints (trigger or send) | 4 |
| Kitchen URL alias mounts (same handlers) | 42 |
| Deprecated endpoints | 0 |

### Email-related endpoints (API behavior)

| Endpoint | Behavior |
|----------|----------|
| `POST /api/v1/auth/register` | Schedules Welcome email (non-blocking) |
| `POST /api/v1/contact` | Awaits contact inbox email via Brevo (502 on failure) |
| `POST /api/v1/orders` | Schedules order confirmation + chef notification |
| `POST /api/v1/admin/test-email` | Awaited Brevo connectivity test (chef) |

### Not implemented

- Dedicated **change-password** endpoint — not present; omit from frontend flows.
- **OTP / Twilio / Resend** — removed; do not integrate against them.

### Frontend checklist

1. Use `Authorization: Bearer <access_token>` on every protected call.
2. Route UI by `data.role` (`customer` | `chef`) after login/register.
3. Prefer `/api/v1/kitchen/*` for the chef dashboard.
4. Call contact/register/orders through this API only — never Brevo from the browser.
5. Keep this `api.md` as the contract; regenerate with `uv run python scripts/generate_api_md.py` after backend route changes.
