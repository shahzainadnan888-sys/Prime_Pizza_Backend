# Users

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /api/v1/users/me`

**Summary:** Get My Profile

**Auth:** Bearer

**Success responses:** `200`

---

## `DELETE /api/v1/users/me`

**Summary:** Soft Delete Account

**Auth:** Bearer

**Success responses:** `200`

---

## `PATCH /api/v1/users/me`

**Summary:** Update My Profile

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `UserProfileUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `full_name` | `nullable` | no |
| `email` | `nullable` | no |

**Success responses:** `200`

---

## `POST /api/v1/users/avatar`

**Summary:** Upload Avatar

**Auth:** Bearer

**Body**

- Content-Type: `multipart/form-data`
- Schema: `Body_upload_avatar_api_v1_users_avatar_post`

| Field | Type | Required |
|-------|------|----------|
| `file` | `string` | yes |

**Success responses:** `200`

---

## `DELETE /api/v1/users/avatar`

**Summary:** Delete Avatar

**Auth:** Bearer

**Success responses:** `200`

---

## `POST /api/v1/users/me/deactivate`

**Summary:** Deactivate Account

**Auth:** Bearer

**Success responses:** `200`

---

## `GET /api/v1/users/addresses`

**Summary:** List Addresses

**Auth:** Bearer

**Success responses:** `200`

---

## `POST /api/v1/users/addresses`

**Summary:** Create Address

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `AddressCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `title` | `string` | yes |
| `recipient_name` | `string` | yes |
| `phone_number` | `string` | yes |
| `street` | `string` | yes |
| `area` | `nullable` | no |
| `city` | `string` | yes |
| `province` | `string` | yes |
| `postal_code` | `string` | yes |
| `country` | `string` | no |
| `latitude` | `nullable` | no |
| `longitude` | `nullable` | no |
| `delivery_notes` | `nullable` | no |
| `is_default` | `boolean` | no |

**Success responses:** `201`

---

## `PATCH /api/v1/users/addresses/{address_id}`

**Summary:** Update Address

**Auth:** Bearer

**Path params**

- `address_id` (string, required)

**Body**

- Content-Type: `application/json`
- Schema: `AddressUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `title` | `nullable` | no |
| `recipient_name` | `nullable` | no |
| `phone_number` | `nullable` | no |
| `street` | `nullable` | no |
| `area` | `nullable` | no |
| `city` | `nullable` | no |
| `province` | `nullable` | no |
| `postal_code` | `nullable` | no |
| `country` | `nullable` | no |
| `latitude` | `nullable` | no |
| `longitude` | `nullable` | no |
| `delivery_notes` | `nullable` | no |
| `is_default` | `nullable` | no |

**Success responses:** `200`

---

## `DELETE /api/v1/users/addresses/{address_id}`

**Summary:** Delete Address

**Auth:** Bearer

**Path params**

- `address_id` (string, required)

**Success responses:** `200`

---

## `PATCH /api/v1/users/addresses/{address_id}/default`

**Summary:** Set Default Address

**Auth:** Bearer

**Path params**

- `address_id` (string, required)

**Success responses:** `200`

---

## `GET /api/v1/users/preferences`

**Summary:** Get Preferences

**Auth:** Bearer

**Success responses:** `200`

---

## `PATCH /api/v1/users/preferences`

**Summary:** Update Preferences

**Auth:** Bearer

**Body**

- Content-Type: `application/json`
- Schema: `PreferenceUpdateRequest`

| Field | Type | Required |
|-------|------|----------|
| `dark_mode` | `nullable` | no |
| `language` | `nullable` | no |
| `marketing_emails` | `nullable` | no |
| `marketing_sms` | `nullable` | no |
| `push_notifications` | `nullable` | no |
| `order_updates` | `nullable` | no |
| `promotional_notifications` | `nullable` | no |
| `preferred_currency` | `nullable` | no |
| `preferred_timezone` | `nullable` | no |

**Success responses:** `200`

---

## `GET /api/v1/users/notifications`

**Summary:** List Notifications

**Auth:** Bearer

**Success responses:** `200`

---

## `PATCH /api/v1/users/notifications/read-all`

**Summary:** Mark All Notifications Read

**Auth:** Bearer

**Success responses:** `200`

---

## `PATCH /api/v1/users/notifications/{notification_id}/read`

**Summary:** Mark Notification Read

**Auth:** Bearer

**Path params**

- `notification_id` (string, required)

**Success responses:** `200`

---

## `DELETE /api/v1/users/notifications/{notification_id}`

**Summary:** Delete Notification

**Auth:** Bearer

**Path params**

- `notification_id` (string, required)

**Success responses:** `200`

---
