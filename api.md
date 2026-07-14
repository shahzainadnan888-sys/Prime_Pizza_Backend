# Prime Pizza API - Frontend Integration Guide

> **For the frontend team.** Everything needed to integrate the backend without reading source code.
>
> Deep per-endpoint docs (large): see [`docs/api/`](docs/api/README.md)  
> Live Swagger (dev): http://127.0.0.1:8000/docs

**Version:** 1.0.0  
**API prefix:** `/api/v1`  
**Auth:** JWT Bearer after phone OTP (local Redis)
**Roles:** `customer` | `owner`

---

## 1. Base URL

| Environment | Example |
|-------------|---------|
| Local | `http://127.0.0.1:8000` |
| Staging | `https://api-staging.yourdomain.com` |
| Production | `https://api.yourdomain.com` |

Business routes: `{BASE_URL}/api/v1/...`

---

## 2. Response format (every endpoint)

### Success

```json
{
  "success": true,
  "message": "Human readable message",
  "data": {},
  "meta": null,
  "request_id": "uuid"
}
```

### Paginated list

```json
{
  "success": true,
  "message": "Success",
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100,
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
  "message": "Human readable error",
  "error": { "code": "validation_error", "details": {} },
  "request_id": "uuid",
  "status_code": 422
}
```

Always check HTTP status + `success` + `error.code`.

---

## 3. Headers

| Header | When | Example |
|--------|------|---------|
| `Content-Type` | JSON POST/PUT/PATCH | `application/json` |
| `Authorization` | Protected routes | `Bearer <access_token>` |
| `X-Request-ID` | Optional tracing | any UUID |
| `Idempotency-Key` | Recommended on `POST /orders` | unique 8-64 char string |

Rate-limit headers on responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Policy`, `Retry-After` (on 429).

---

## 4. Authentication (must implement first)

```text
1. POST /api/v1/auth/send-otp     { "phone_number": "+923001234567" }
2. User enters the 6-digit OTP
3. POST /api/v1/auth/verify-otp   { "phone_number": "+923001234567", "code": "123456" }
4. Save data.tokens.access_token + data.tokens.refresh_token
5. Send Authorization: Bearer <access_token> on protected calls
6. On 401 expired_token → POST /api/v1/auth/refresh { "refresh_token": "..." }
7. Logout → POST /api/v1/auth/logout (Bearer) optional body { "refresh_token" }
```

**Phone:** E.164 only (`+923001234567`).

### Where does the OTP come from?

The backend uses a **local OTP provider** — no SMS is sent. A cryptographically
secure 6-digit code is generated, stored in Redis for **5 minutes**, and **printed
in the backend terminal**:

```text
==================================================
Development OTP

Phone: +923348957141

OTP: 483921

Expires In: 5 Minutes
==================================================
```

**Development only:** `POST /api/v1/auth/send-otp` also returns the code in the
response body so you can auto-fill it while building:

```json
{
  "success": true,
  "message": "Verification code sent",
  "data": {
    "phone_number": "+923001234567",
    "expires_in": 300,
    "message": "Verification code sent",
    "otp": "483921"
  }
}
```

> ⚠️ The `otp` field is present **only when the server runs with `APP_ENV=development`**.
> In staging/production the field is absent. Never depend on it — always keep the
> manual OTP entry screen as the real path.

**OTP rules the UI should handle:**

| Rule | Value | Frontend behaviour |
|------|-------|--------------------|
| Code length | 6 digits | numeric input, `inputmode="numeric"` |
| Expiry | 300s (5 min) | show countdown from `data.expires_in` |
| Max wrong attempts | 5 | after 5, the code is destroyed → send a new one |
| Resend limit | 3 per 10 min per phone | disable “Resend” until the window clears |
| Wrong code | `400 invalid_otp` | show inline error, let user retry |
| Expired / used code | `400 expired_otp` | prompt “Request a new code” |
| Too many requests | `429 rate_limit_exceeded` | wait `Retry-After` seconds |

**Tokens:**

| Token | Default lifetime | Note |
|-------|------------------|------|
| access | ~30 min (`expires_in`) | Put in Authorization header |
| refresh | ~30 days | Rotates on each refresh; discard old one |

**Roles:**

| Role | Meaning |
|------|---------|
| `customer` | Shopper app |
| `owner` | Dashboard (`/api/v1/admin/*`) — phone must match server `OWNER_PHONE_NUMBER` |

Confirm role via `GET /api/v1/auth/me` or `GET /api/v1/users/me`.

### Verify OTP success (example)

```json
{
  "success": true,
  "message": "Authentication successful",
  "data": {
    "user": {
      "id": "uuid",
      "phone_number": "+923001234567",
      "full_name": "Guest",
      "role": "customer",
      "is_verified": true,
      "is_active": true,
      "created_at": "2026-01-15T12:00:00Z"
    },
    "tokens": {
      "access_token": "<jwt>",
      "refresh_token": "<jwt>",
      "token_type": "bearer",
      "expires_in": 1800
    },
    "is_new_user": true
  }
}
```

---

## 5. Who can call what

| Area | Auth |
|------|------|
| Health, Catalog GET (categories/products/deals/search) | Public |
| Auth send-otp / verify-otp / refresh | Public |
| Auth logout / me | Bearer |
| Users, Cart, Wishlist, Checkout, Orders | Bearer + verified customer |
| All `/api/v1/admin/*` | Bearer + **owner** |

If a customer asks for someone else’s order/address → API returns **404** (not 403).

---

## 6. Customer journey (copy this order)

```text
GET  /api/v1/categories
GET  /api/v1/products
GET  /api/v1/products/{slug}
POST /api/v1/auth/send-otp → verify-otp
POST /api/v1/cart/items
POST /api/v1/users/addresses
POST /api/v1/cart/apply-coupon          (optional)
POST /api/v1/checkout/validate
POST /api/v1/orders                     (+ Idempotency-Key header or body)
GET  /api/v1/orders/{id}/tracking
```

---

## 7. Owner journey

```text
OTP login with owner phone
GET  /api/v1/admin/dashboard
GET  /api/v1/admin/orders
PATCH /api/v1/admin/orders/{id}/status
POST /api/v1/admin/products
POST /api/v1/admin/products/{id}/images   (multipart)
```

---

## 8. Money, IDs, dates

- IDs are UUIDs.
- Public catalog uses **slugs**; admin uses **UUIDs**.
- Money is decimal-safe JSON (string or number — treat as decimal).
- Timestamps are ISO-8601 UTC.

---

## 9. File uploads

| Endpoint | Form field | Limits |
|----------|------------|--------|
| `POST /api/v1/users/avatar` | `file` | ~5MB, jpeg/png/webp/gif |
| `POST /api/v1/admin/products/{id}/images` | `file`, optional `alt_text`, `is_primary` | same |

Do not set `Content-Type` manually when using `FormData`.

---

## 10. Pagination

`page` (default 1), `page_size` (default 20, max 100).

Product `sort`: `newest` | `oldest` | `price_asc` | `price_desc` | `popularity` | `name_asc` | `name_desc` | `preparation_time`

---

## 11. Enums (use exactly these strings)

**OrderStatus:** `pending`, `confirmed`, `preparing`, `ready`, `out_for_delivery`, `delivered`, `cancelled`, `refunded`

**PaymentMethod:** `cash_on_delivery`, `card`, `online`, `wallet`

**PaymentStatus:** `pending`, `paid`, `failed`, `refunded`, `partially_refunded`, `cancelled`

**StockStatus:** `in_stock`, `out_of_stock`, `limited`

**CouponType:** `percentage`, `fixed`

**UserRole:** `customer`, `owner`

---

## 12. Error codes

| HTTP | code | Frontend action |
|------|------|-----------------|
| 400 | `invalid_otp` | wrong code — show inline error, allow retry (max 5) |
| 400 | `expired_otp` | code expired/consumed — prompt “Request a new code” |
| 401 | `unauthorized` / `invalid_token` / `expired_token` | refresh or login |
| 403 | `forbidden` | hide feature |
| 404 | `not_found` | not found UI |
| 409 | `conflict` | show conflict |
| 413 | `payload_too_large` | smaller body/file |
| 422 | `validation_error` | map `details` to fields |
| 429 | `rate_limit_exceeded` | wait `Retry-After` |
| 503 | `maintenance_mode` | maintenance screen |

---

## 13. CORS

Origin must match server `FRONTEND_URL`. Auth via Bearer header (no cookies / CSRF).

---

## 14. TypeScript helper

```typescript
const BASE = import.meta.env.VITE_API_BASE; // e.g. http://127.0.0.1:8000

type Ok<T> = {
  success: true;
  message: string;
  data: T;
  meta?: Record<string, unknown> | null;
  request_id?: string | null;
};

type Err = {
  success: false;
  message: string;
  error: { code: string; details?: unknown };
  status_code?: number;
};

export async function api<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<Ok<T>> {
  const headers = new Headers(init.headers);
  if (init.token) headers.set("Authorization", `Bearer ${init.token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const json = (await res.json()) as Ok<T> | Err;
  if (!res.ok || json.success === false) throw json;
  return json as Ok<T>;
}
```

---

## 15. Endpoint index (quick reference)

Full details for each route: [`docs/api/`](docs/api/README.md)


| Tag | Endpoints | Doc file |
|-----|-----------|----------|
| Health | 10 | [`health.md`](docs/api/health.md) |
| Authentication | 5 | [`authentication.md`](docs/api/authentication.md) |
| Users | 17 | [`users.md`](docs/api/users.md) |
| Catalog | 10 | [`catalog.md`](docs/api/catalog.md) |
| Cart | 8 | [`cart.md`](docs/api/cart.md) |
| Wishlist | 4 | [`wishlist.md`](docs/api/wishlist.md) |
| Checkout | 1 | [`checkout.md`](docs/api/checkout.md) |
| Orders | 5 | [`orders.md`](docs/api/orders.md) |
| Admin Catalog | 24 | [`admin-catalog.md`](docs/api/admin-catalog.md) |
| Admin Orders | 5 | [`admin-orders.md`](docs/api/admin-orders.md) |
| Admin Email | 1 | [`admin-email.md`](docs/api/admin-email.md) |
| Admin Dashboard | 3 | [`admin-dashboard.md`](docs/api/admin-dashboard.md) |
| Admin Customers | 4 | [`admin-customers.md`](docs/api/admin-customers.md) |
| Admin Coupons | 8 | [`admin-coupons.md`](docs/api/admin-coupons.md) |
| Admin Notifications | 3 | [`admin-notifications.md`](docs/api/admin-notifications.md) |
| Admin Settings | 5 | [`admin-settings.md`](docs/api/admin-settings.md) |
| Admin Audit | 1 | [`admin-audit.md`](docs/api/admin-audit.md) |
| Admin Search | 1 | [`admin-search.md`](docs/api/admin-search.md) |

### All routes (one-liners)

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/` | Public | API root |
| `GET` | `/health` | Public | Liveness probe |
| `GET` | `/health/database` | Public | Database readiness |
| `GET` | `/health/redis` | Public | Redis readiness |
| `GET` | `/health/services` | Public | Dependency and configuration readiness |
| `GET` | `/api/v1/` | Public | API root |
| `GET` | `/api/v1/health` | Public | Liveness probe |
| `GET` | `/api/v1/health/database` | Public | Database readiness |
| `GET` | `/api/v1/health/redis` | Public | Redis readiness |
| `GET` | `/api/v1/health/services` | Public | Dependency and configuration readiness |
| `POST` | `/api/v1/auth/send-otp` | Public | Send OTP (local Redis provider) |
| `POST` | `/api/v1/auth/verify-otp` | Public | Verify OTP and issue tokens |
| `POST` | `/api/v1/auth/refresh` | Public | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Bearer | Logout and revoke tokens |
| `GET` | `/api/v1/auth/me` | Bearer | Current authenticated user |
| `GET` | `/api/v1/users/me` | Bearer | Get My Profile |
| `DELETE` | `/api/v1/users/me` | Bearer | Soft Delete Account |
| `PATCH` | `/api/v1/users/me` | Bearer | Update My Profile |
| `POST` | `/api/v1/users/avatar` | Bearer | Upload Avatar |
| `DELETE` | `/api/v1/users/avatar` | Bearer | Delete Avatar |
| `POST` | `/api/v1/users/me/deactivate` | Bearer | Deactivate Account |
| `GET` | `/api/v1/users/addresses` | Bearer | List Addresses |
| `POST` | `/api/v1/users/addresses` | Bearer | Create Address |
| `PATCH` | `/api/v1/users/addresses/{address_id}` | Bearer | Update Address |
| `DELETE` | `/api/v1/users/addresses/{address_id}` | Bearer | Delete Address |
| `PATCH` | `/api/v1/users/addresses/{address_id}/default` | Bearer | Set Default Address |
| `GET` | `/api/v1/users/preferences` | Bearer | Get Preferences |
| `PATCH` | `/api/v1/users/preferences` | Bearer | Update Preferences |
| `GET` | `/api/v1/users/notifications` | Bearer | List Notifications |
| `PATCH` | `/api/v1/users/notifications/read-all` | Bearer | Mark All Notifications Read |
| `PATCH` | `/api/v1/users/notifications/{notification_id}/read` | Bearer | Mark Notification Read |
| `DELETE` | `/api/v1/users/notifications/{notification_id}` | Bearer | Delete Notification |
| `GET` | `/api/v1/categories` | Public | List Categories |
| `GET` | `/api/v1/categories/{slug}` | Public | Get Category |
| `GET` | `/api/v1/products` | Public | List Products |
| `GET` | `/api/v1/products/search` | Public | Search Products |
| `GET` | `/api/v1/products/featured` | Public | Featured Products |
| `GET` | `/api/v1/products/popular` | Public | Popular Products |
| `GET` | `/api/v1/products/recommended` | Public | Recommended Products |
| `GET` | `/api/v1/products/{slug}` | Public | Get Product |
| `GET` | `/api/v1/deals` | Public | List Deals |
| `GET` | `/api/v1/deals/{slug}` | Public | Get Deal |
| `GET` | `/api/v1/cart` | Bearer | Get Cart |
| `GET` | `/api/v1/cart/summary` | Bearer | Get Cart Summary |
| `POST` | `/api/v1/cart/items` | Bearer | Add Cart Item |
| `PATCH` | `/api/v1/cart/items/{item_id}` | Bearer | Update Cart Item |
| `DELETE` | `/api/v1/cart/items/{item_id}` | Bearer | Remove Cart Item |
| `DELETE` | `/api/v1/cart/clear` | Bearer | Clear Cart |
| `POST` | `/api/v1/cart/apply-coupon` | Bearer | Apply Coupon |
| `DELETE` | `/api/v1/cart/remove-coupon` | Bearer | Remove Coupon |
| `GET` | `/api/v1/wishlist` | Bearer | Get Wishlist |
| `POST` | `/api/v1/wishlist` | Bearer | Add Wishlist Item |
| `DELETE` | `/api/v1/wishlist/clear` | Bearer | Clear Wishlist |
| `DELETE` | `/api/v1/wishlist/{product_id}` | Bearer | Remove Wishlist Item |
| `POST` | `/api/v1/checkout/validate` | Bearer | Validate Checkout |
| `POST` | `/api/v1/orders` | Bearer | Place Order |
| `GET` | `/api/v1/orders` | Bearer | List My Orders |
| `GET` | `/api/v1/orders/{order_id}` | Bearer | Get My Order |
| `GET` | `/api/v1/orders/{order_id}/tracking` | Bearer | Track My Order |
| `PATCH` | `/api/v1/orders/{order_id}/cancel` | Bearer | Cancel My Order |
| `GET` | `/api/v1/admin/categories` | Bearer + owner | List Admin Categories |
| `POST` | `/api/v1/admin/categories` | Bearer + owner | Create Category |
| `PATCH` | `/api/v1/admin/categories/reorder` | Bearer + owner | Reorder Categories |
| `PATCH` | `/api/v1/admin/categories/{category_id}` | Bearer + owner | Update Category |
| `DELETE` | `/api/v1/admin/categories/{category_id}` | Bearer + owner | Delete Category |
| `PATCH` | `/api/v1/admin/categories/{category_id}/hide` | Bearer + owner | Hide Category |
| `PATCH` | `/api/v1/admin/categories/{category_id}/restore` | Bearer + owner | Restore Category |
| `POST` | `/api/v1/admin/products` | Bearer + owner | Create Product |
| `PATCH` | `/api/v1/admin/products/{product_id}` | Bearer + owner | Update Product |
| `DELETE` | `/api/v1/admin/products/{product_id}` | Bearer + owner | Delete Product |
| `POST` | `/api/v1/admin/products/{product_id}/images` | Bearer + owner | Upload Product Image |
| `DELETE` | `/api/v1/admin/products/{product_id}/images/{image_id}` | Bearer + owner | Delete Product Image |
| `PATCH` | `/api/v1/admin/products/{product_id}/images/reorder` | Bearer + owner | Reorder Product Images |
| `POST` | `/api/v1/admin/deals` | Bearer + owner | Create Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}` | Bearer + owner | Update Deal |
| `DELETE` | `/api/v1/admin/deals/{deal_id}` | Bearer + owner | Delete Deal |
| `POST` | `/api/v1/admin/products/bulk/visibility` | Bearer + owner | Bulk Product Visibility |
| `POST` | `/api/v1/admin/products/bulk/featured` | Bearer + owner | Bulk Product Featured |
| `POST` | `/api/v1/admin/products/bulk/availability` | Bearer + owner | Bulk Product Availability |
| `POST` | `/api/v1/admin/products/bulk/category` | Bearer + owner | Bulk Product Category |
| `POST` | `/api/v1/admin/products/bulk/delete` | Bearer + owner | Bulk Product Delete |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/activate` | Bearer + owner | Activate Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/deactivate` | Bearer + owner | Deactivate Deal |
| `PATCH` | `/api/v1/admin/deals/{deal_id}/schedule` | Bearer + owner | Schedule Deal |
| `GET` | `/api/v1/admin/orders` | Bearer + owner | List Orders |
| `GET` | `/api/v1/admin/orders/{order_id}` | Bearer + owner | Get Order |
| `PATCH` | `/api/v1/admin/orders/{order_id}/status` | Bearer + owner | Update Order Status |
| `PATCH` | `/api/v1/admin/orders/{order_id}/payment` | Bearer + owner | Update Payment Status |
| `PATCH` | `/api/v1/admin/orders/{order_id}/notes` | Bearer + owner | Update Order Notes |
| `POST` | `/api/v1/admin/test-email` | Bearer + owner | Send Test Email |
| `GET` | `/api/v1/admin/dashboard` | Bearer + owner | Get Dashboard |
| `GET` | `/api/v1/admin/analytics` | Bearer + owner | Get Analytics |
| `GET` | `/api/v1/admin/charts` | Bearer + owner | Get Charts |
| `GET` | `/api/v1/admin/customers` | Bearer + owner | List Customers |
| `GET` | `/api/v1/admin/customers/{customer_id}` | Bearer + owner | Get Customer |
| `PATCH` | `/api/v1/admin/customers/{customer_id}` | Bearer + owner | Update Customer |
| `PATCH` | `/api/v1/admin/customers/{customer_id}/status` | Bearer + owner | Update Customer Status |
| `GET` | `/api/v1/admin/coupons` | Bearer + owner | List Coupons |
| `POST` | `/api/v1/admin/coupons` | Bearer + owner | Create Coupon |
| `GET` | `/api/v1/admin/coupons/{coupon_id}` | Bearer + owner | Get Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}` | Bearer + owner | Update Coupon |
| `DELETE` | `/api/v1/admin/coupons/{coupon_id}` | Bearer + owner | Delete Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}/enable` | Bearer + owner | Enable Coupon |
| `PATCH` | `/api/v1/admin/coupons/{coupon_id}/disable` | Bearer + owner | Disable Coupon |
| `GET` | `/api/v1/admin/coupons/{coupon_id}/usage` | Bearer + owner | Get Coupon Usage |
| `POST` | `/api/v1/admin/notifications` | Bearer + owner | Create Notification |
| `POST` | `/api/v1/admin/notifications/broadcast` | Bearer + owner | Broadcast Notification |
| `DELETE` | `/api/v1/admin/notifications/{notification_id}` | Bearer + owner | Delete Notification |
| `GET` | `/api/v1/admin/settings` | Bearer + owner | List Settings |
| `PUT` | `/api/v1/admin/settings` | Bearer + owner | Bulk Update Settings |
| `GET` | `/api/v1/admin/settings/restaurant` | Bearer + owner | Get Restaurant Settings |
| `GET` | `/api/v1/admin/settings/{key}` | Bearer + owner | Get Setting |
| `PUT` | `/api/v1/admin/settings/{key}` | Bearer + owner | Upsert Setting |
| `GET` | `/api/v1/admin/audit-logs` | Bearer + owner | List Audit Logs |
| `POST` | `/api/v1/admin/search` | Bearer + owner | Admin Search |

---

Regenerate docs:

```bash
python scripts/generate_api_md.py
```
