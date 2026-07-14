# Admin Settings

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/admin/settings`

**Summary:** List Settings

**Auth:** Bearer + owner

**Success responses:** `200`

---

## `PUT /api/v1/admin/settings`

**Summary:** Bulk Update Settings

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `SystemSettingsBulkUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `settings` | `object` | yes |

**Success responses:** `200`

---

## `GET /api/v1/admin/settings/restaurant`

**Summary:** Get Restaurant Settings

**Auth:** Bearer + owner

**Success responses:** `200`

---

## `GET /api/v1/admin/settings/{key}`

**Summary:** Get Setting

**Auth:** Bearer + owner

**Path params**

- `key` (string, required)

**Success responses:** `200`

---

## `PUT /api/v1/admin/settings/{key}`

**Summary:** Upsert Setting

**Auth:** Bearer + owner

**Path params**

- `key` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `SystemSettingUpsertRequest`

| Field | Type | Required |
|-------|------|----------|
| `value` | `nullable` | no |
| `value_json` | `nullable` | no |
| `description` | `nullable` | no |
| `is_public` | `nullable` | no |

**Success responses:** `200`

---
