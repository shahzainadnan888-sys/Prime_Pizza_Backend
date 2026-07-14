# Wishlist

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/wishlist`

**Summary:** Get Wishlist

**Auth:** Bearer

**Success responses:** `200`

---

## `POST /api/v1/wishlist`

**Summary:** Add Wishlist Item

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `WishlistAddRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_id` | `string` | yes |

**Success responses:** `201`

---

## `DELETE /api/v1/wishlist/clear`

**Summary:** Clear Wishlist

**Auth:** Bearer

**Success responses:** `200`

---

## `DELETE /api/v1/wishlist/{product_id}`

**Summary:** Remove Wishlist Item

**Auth:** Bearer

**Path params**

- `product_id` (string, required)

**Success responses:** `200`

---
