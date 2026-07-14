# Admin Catalog

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/categories`

**Summary:** List Admin Categories

**Auth:** Bearer + owner

**Success responses:** `200`

---

## `POST /api/v1/admin/categories`

**Summary:** Create Category

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `CategoryCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `name` | `string` | yes |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `image_url` | `nullable` | no |
| `display_order` | `integer` | no |
| `is_visible` | `boolean` | no |
| `seo_title` | `nullable` | no |
| `seo_description` | `nullable` | no |
| `seo_keywords` | `nullable` | no |

**Success responses:** `201`

---

## `PATCH /api/v1/admin/categories/reorder`

**Summary:** Reorder Categories

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `CategoryReorderRequest`

| Field | Type | Required |
|-------|------|----------|
| `items` | `array` | yes |

**Success responses:** `200`

---

## `PATCH /api/v1/admin/categories/{category_id}`

**Summary:** Update Category

**Auth:** Bearer + owner

**Path params**

- `category_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `CategoryUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `name` | `nullable` | no |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `image_url` | `nullable` | no |
| `display_order` | `nullable` | no |
| `is_visible` | `nullable` | no |
| `seo_title` | `nullable` | no |
| `seo_description` | `nullable` | no |
| `seo_keywords` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/admin/categories/{category_id}`

**Summary:** Delete Category

**Auth:** Bearer + owner

**Path params**

- `category_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/categories/{category_id}/hide`

**Summary:** Hide Category

**Auth:** Bearer + owner

**Path params**

- `category_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/categories/{category_id}/restore`

**Summary:** Restore Category

**Auth:** Bearer + owner

**Path params**

- `category_id` (string, required)

**Success responses:** `200`

---

## `POST /api/v1/admin/products`

**Summary:** Create Product

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `category_id` | `string` | yes |
| `name` | `string` | yes |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `short_description` | `nullable` | no |
| `base_price` | `nullable` | yes |
| `discount_price` | `nullable` | no |
| `image_url` | `nullable` | no |
| `is_available` | `boolean` | no |
| `stock_status` | `StockStatus` | no |
| `preparation_time_minutes` | `nullable` | no |
| `calories` | `nullable` | no |
| `is_featured` | `boolean` | no |
| `is_popular` | `boolean` | no |
| `is_best_seller` | `boolean` | no |
| `is_visible` | `boolean` | no |
| `sort_order` | `integer` | no |
| `tags` | `array` | no |
| `seo_title` | `nullable` | no |
| `seo_description` | `nullable` | no |
| `seo_keywords` | `nullable` | no |
| `variants` | `array` | no |
| `extra_option_ids` | `array` | no |

**Success responses:** `201`

---

## `PATCH /api/v1/admin/products/{product_id}`

**Summary:** Update Product

**Auth:** Bearer + owner

**Path params**

- `product_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `ProductUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `category_id` | `nullable` | no |
| `name` | `nullable` | no |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `short_description` | `nullable` | no |
| `base_price` | `nullable` | no |
| `discount_price` | `nullable` | no |
| `image_url` | `nullable` | no |
| `is_available` | `nullable` | no |
| `stock_status` | `nullable` | no |
| `preparation_time_minutes` | `nullable` | no |
| `calories` | `nullable` | no |
| `is_featured` | `nullable` | no |
| `is_popular` | `nullable` | no |
| `is_best_seller` | `nullable` | no |
| `is_visible` | `nullable` | no |
| `sort_order` | `nullable` | no |
| `tags` | `nullable` | no |
| `seo_title` | `nullable` | no |
| `seo_description` | `nullable` | no |
| `seo_keywords` | `nullable` | no |
| `variants` | `nullable` | no |
| `extra_option_ids` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/admin/products/{product_id}`

**Summary:** Delete Product

**Auth:** Bearer + owner

**Path params**

- `product_id` (string, required)

**Success responses:** `200`

---

## `POST /api/v1/admin/products/{product_id}/images`

**Summary:** Upload Product Image

**Auth:** Bearer + owner

**Path params**

- `product_id` (string, required)

**Body**

- Content-Type: `multipart/form-data`
- Schema: `Body_upload_product_image_api_v1_admin_products__product_id__images_post`

| Field | Type | Required |
|-------|------|----------|
| `file` | `string` | yes |
| `alt_text` | `nullable` | no |
| `is_primary` | `boolean` | no |

**Success responses:** `201`

---

## `DELETE /api/v1/admin/products/{product_id}/images/{image_id}`

**Summary:** Delete Product Image

**Auth:** Bearer + owner

**Path params**

- `product_id` (string, required)
- `image_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/products/{product_id}/images/reorder`

**Summary:** Reorder Product Images

**Auth:** Bearer + owner

**Path params**

- `product_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `ImageReorderRequest`

| Field | Type | Required |
|-------|------|----------|
| `image_ids` | `array` | yes |

**Success responses:** `200`

---

## `POST /api/v1/admin/deals`

**Summary:** Create Deal

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `DealCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `name` | `string` | yes |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `deal_type` | `DealType` | yes |
| `deal_price` | `nullable` | yes |
| `discount_percent` | `nullable` | no |
| `image_url` | `nullable` | no |
| `is_active` | `boolean` | no |
| `is_visible` | `boolean` | no |
| `starts_at` | `nullable` | no |
| `ends_at` | `nullable` | no |
| `products` | `array` | no |

**Success responses:** `201`

---

## `PATCH /api/v1/admin/deals/{deal_id}`

**Summary:** Update Deal

**Auth:** Bearer + owner

**Path params**

- `deal_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `DealUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `name` | `nullable` | no |
| `slug` | `nullable` | no |
| `description` | `nullable` | no |
| `deal_type` | `nullable` | no |
| `deal_price` | `nullable` | no |
| `discount_percent` | `nullable` | no |
| `image_url` | `nullable` | no |
| `is_active` | `nullable` | no |
| `is_visible` | `nullable` | no |
| `starts_at` | `nullable` | no |
| `ends_at` | `nullable` | no |
| `products` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/admin/deals/{deal_id}`

**Summary:** Delete Deal

**Auth:** Bearer + owner

**Path params**

- `deal_id` (string, required)

**Success responses:** `200`

---

## `POST /api/v1/admin/products/bulk/visibility`

**Summary:** Bulk Product Visibility

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductBulkVisibilityRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_ids` | `array` | yes |
| `is_visible` | `boolean` | yes |

**Success responses:** `200`

---

## `POST /api/v1/admin/products/bulk/featured`

**Summary:** Bulk Product Featured

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductBulkFeaturedRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_ids` | `array` | yes |
| `is_featured` | `boolean` | yes |

**Success responses:** `200`

---

## `POST /api/v1/admin/products/bulk/availability`

**Summary:** Bulk Product Availability

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductBulkAvailabilityRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_ids` | `array` | yes |
| `is_available` | `boolean` | yes |

**Success responses:** `200`

---

## `POST /api/v1/admin/products/bulk/category`

**Summary:** Bulk Product Category

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductBulkCategoryRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_ids` | `array` | yes |
| `category_id` | `string` | yes |

**Success responses:** `200`

---

## `POST /api/v1/admin/products/bulk/delete`

**Summary:** Bulk Product Delete

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `ProductBulkDeleteRequest`

| Field | Type | Required |
|-------|------|----------|
| `product_ids` | `array` | yes |

**Success responses:** `200`

---

## `PATCH /api/v1/admin/deals/{deal_id}/activate`

**Summary:** Activate Deal

**Auth:** Bearer + owner

**Path params**

- `deal_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/deals/{deal_id}/deactivate`

**Summary:** Deactivate Deal

**Auth:** Bearer + owner

**Path params**

- `deal_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/admin/deals/{deal_id}/schedule`

**Summary:** Schedule Deal

**Auth:** Bearer + owner

**Path params**

- `deal_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `DealScheduleRequest`

| Field | Type | Required |
|-------|------|----------|
| `starts_at` | `nullable` | no |
| `ends_at` | `nullable` | no |
| `is_active` | `nullable` | no |
| `is_visible` | `nullable` | no |

**Success responses:** `200`

---
