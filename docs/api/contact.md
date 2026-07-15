# Contact

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
