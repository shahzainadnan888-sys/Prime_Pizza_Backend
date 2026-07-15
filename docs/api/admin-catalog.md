# Admin Catalog

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
