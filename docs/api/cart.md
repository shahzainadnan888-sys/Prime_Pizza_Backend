# Cart

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/cart`

**Summary:** Get Cart

**Auth:** Bearer

**Success responses:** `200`

---

## `GET /api/v1/cart/summary`

**Summary:** Get Cart Summary

**Auth:** Bearer

**Success responses:** `200`

---

## `POST /api/v1/cart/items`

**Summary:** Add Cart Item

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `AddCartItemRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_id` | `string` | yes |
| `variant_id` | `nullable` | no |
| `quantity` | `integer` | no |
| `extra_option_ids` | `array` | no |
| `extras` | `array` | no |
| `special_instructions` | `nullable` | no |

**Success responses:** `201`

---

## `PATCH /api/v1/cart/items/{item_id}`

**Summary:** Update Cart Item

**Auth:** Bearer

**Path params**

- `item_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `UpdateCartItemRequest`

| Field | Type | Required |
|-------|------|----------|
| `quantity` | `nullable` | no |
| `special_instructions` | `nullable` | no |
| `extra_option_ids` | `nullable` | no |
| `extras` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/cart/items/{item_id}`

**Summary:** Remove Cart Item

**Auth:** Bearer

**Path params**

- `item_id` (string, required)

**Success responses:** `200`

---

## `DELETE /api/v1/cart/clear`

**Summary:** Clear Cart

**Auth:** Bearer

**Success responses:** `200`

---

## `POST /api/v1/cart/apply-coupon`

**Summary:** Apply Coupon

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `ApplyCouponRequest`

| Field | Type | Required |
|-------|------|----------|
| `code` | `string` | yes |

**Success responses:** `200`

---

## `DELETE /api/v1/cart/remove-coupon`

**Summary:** Remove Coupon

**Auth:** Bearer

**Success responses:** `200`

---
