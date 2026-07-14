# Admin Notifications

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `POST /api/v1/admin/notifications`

**Summary:** Create Notification

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `NotificationCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `user_id` | `nullable` | no |
| `title` | `string` | yes |
| `message` | `string` | yes |
| `notification_type` | `NotificationType` | no |
| `payload` | `nullable` | no |
| `scheduled_at` | `nullable` | no |

**Success responses:** `201`

---

## `POST /api/v1/admin/notifications/broadcast`

**Summary:** Broadcast Notification

**Auth:** Bearer + owner

**Body**

- Content-Type: `application/json`
- Schema: `NotificationBroadcastRequest`

| Field | Type | Required |
|-------|------|----------|
| `title` | `string` | yes |
| `message` | `string` | yes |
| `notification_type` | `NotificationType` | no |
| `payload` | `nullable` | no |
| `role_filter` | `nullable` | no |
| `scheduled_at` | `nullable` | no |

**Success responses:** `201`

---

## `DELETE /api/v1/admin/notifications/{notification_id}`

**Summary:** Delete Notification

**Auth:** Bearer + owner

**Path params**

- `notification_id` (string, required)

**Success responses:** `200`

---
