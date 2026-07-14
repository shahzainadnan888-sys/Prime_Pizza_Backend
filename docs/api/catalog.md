# Catalog

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/categories`

**Summary:** List Categories

**Auth:** Public

**Success responses:** `200`

---

## `GET /api/v1/categories/{slug}`

**Summary:** Get Category

**Auth:** Public

**Path params**

- `slug` (string, required)

**Success responses:** `200`

---

## `GET /api/v1/products`

**Summary:** List Products

**Auth:** Public

**Query params**

- `category` (object, default=``)
- `category_id` (object, default=``)
- `min_price` (object, default=``)
- `max_price` (object, default=``)
- `is_available` (object, default=``)
- `is_featured` (object, default=``)
- `is_popular` (object, default=``)
- `is_best_seller` (object, default=``)
- `vegetarian` (object, default=``)
- `tag` (object, default=``)
- `min_calories` (object, default=``)
- `max_calories` (object, default=``)
- `max_preparation_time` (object, default=``)
- `sort` (ProductSort, default=`newest`)
- `q` (object, default=``)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `GET /api/v1/products/search`

**Summary:** Search Products

**Auth:** Public

**Query params**

- `q` (string, default=``)
- `page` (integer, default=`1`)
- `page_size` (integer, default=`20`)

**Success responses:** `200`

---

## `GET /api/v1/products/featured`

**Summary:** Featured Products

**Auth:** Public

**Success responses:** `200`

---

## `GET /api/v1/products/popular`

**Summary:** Popular Products

**Auth:** Public

**Success responses:** `200`

---

## `GET /api/v1/products/recommended`

**Summary:** Recommended Products

**Auth:** Public

**Query params**

- `product_slug` (object, default=``)
- `category` (object, default=``)

**Success responses:** `200`

---

## `GET /api/v1/products/{slug}`

**Summary:** Get Product

**Auth:** Public

**Path params**

- `slug` (string, required)

**Success responses:** `200`

---

## `GET /api/v1/deals`

**Summary:** List Deals

**Auth:** Public

**Success responses:** `200`

---

## `GET /api/v1/deals/{slug}`

**Summary:** Get Deal

**Auth:** Public

**Path params**

- `slug` (string, required)

**Success responses:** `200`

---
