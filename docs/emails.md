# Transactional Email Notifications

Resend-backed ownership notifications. Marketing / promo / newsletter out of scope.

## Trigger

1. Customer places order
2. Checkout transaction **commits**
3. `OrderService` builds an `OrderEmailPayload` snapshot
4. `EmailService.notify_owner_new_order` enqueues an asyncio task
5. Background task renders HTML + text, retries Resend send, writes `email_logs`

Order API responses do **not** wait for Resend. Email failures never roll back orders.

## Configuration (.env only)

| Variable | Purpose |
|----------|---------|
| `RESEND_API_KEY` | Provider key |
| `RESEND_FROM_EMAIL` | From address (dev onboarding sender or verified domain) |
| `OWNER_EMAIL` | Primary owner recipient |
| `OWNER_NOTIFICATION_EMAILS` | Optional comma-separated extra owners |
| `EMAIL_ENABLED` | Kill switch |
| `EMAIL_MAX_RETRIES` | Attempts (default 3) |
| `EMAIL_LOGO_URL` | Optional logo for HTML header |

Switching from Resend test sender → `support@primepizza.com` requires **only** updating `RESEND_FROM_EMAIL`.

## Owner test

`POST /api/v1/admin/test-email` (permission `email.test`)

## Templates

- `owner_new_order` — live
- `owner_test` — live
- `order_confirmation` / `order_cancelled` / `order_delivered` — stubs for customer emails
