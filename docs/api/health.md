# Health

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
