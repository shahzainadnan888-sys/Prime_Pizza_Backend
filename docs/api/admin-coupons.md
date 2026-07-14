# Admin Coupons

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/coupons`

**Summary:** List Coupons

**Auth:** Bearer + owner

**Query params**

- `q` (object, default=``)
- `is_active` (object, default=``)
- `coupon_type` (object, default=``)
- `sort` (string, default=`newest`)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `POST /api/v1/admin/coupons`

**Summary:** Create Coupon

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `CouponCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `code` | `string` | yes |
| `description` | `nullable` | no |
| `coupon_type` | `CouponType` | yes |
| `value` | `nullable` | yes |
| `minimum_order_amount` | `nullable` | no |
| `maximum_discount` | `nullable` | no |
| `usage_limit` | `nullable` | no |
| `per_user_limit` | `nullable` | no |
| `is_active` | `boolean` | no |
| `starts_at` | `nullable` | no |
| `expires_at` | `nullable` | no |

**Success responses:** `201`

---

## `GET /api/v1/admin/coupons/{coupon_id}`

**Summary:** Get Coupon

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/coupons/{coupon_id}`

**Summary:** Update Coupon

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `CouponUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `description` | `nullable` | no |
| `coupon_type` | `nullable` | no |
| `value` | `nullable` | no |
| `minimum_order_amount` | `nullable` | no |
| `maximum_discount` | `nullable` | no |
| `usage_limit` | `nullable` | no |
| `per_user_limit` | `nullable` | no |
| `is_active` | `nullable` | no |
| `starts_at` | `nullable` | no |
| `expires_at` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/admin/coupons/{coupon_id}`

**Summary:** Delete Coupon

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/coupons/{coupon_id}/enable`

**Summary:** Enable Coupon

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/coupons/{coupon_id}/disable`

**Summary:** Disable Coupon

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Success responses:** `200`

---

## `GET /api/v1/admin/coupons/{coupon_id}/usage`

**Summary:** Get Coupon Usage

**Auth:** Bearer + owner

**Path params**

- `coupon_id` (string, required)

**Success responses:** `200`

---
