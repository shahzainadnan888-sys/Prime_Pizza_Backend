# Email (Brevo)

Transactional email via Brevo. Marketing / promo / newsletter out of scope.

## Flow

1. Business action commits (register / order / contact)
2. Service enqueues email through `EmailService` (`InProcessEmailQueue`)
3. Background task renders HTML templates, retries Brevo send, writes `email_logs`
4. Failures are logged — primary API success is never rolled back

## Templates (`app/templates/`)

| File | Trigger |
|------|---------|
| `welcome_email.html` | Customer registration |
| `order_notification.html` | Customer places order → `ADMIN_EMAIL` |
| `contact_notification.html` | Contact form → admin |
| `contact_confirmation.html` | Contact form → customer |

## Environment

| Variable | Purpose |
|----------|---------|
| `BREVO_API_KEY` | Provider key |
| `BREVO_SENDER_NAME` | From display name |
| `BREVO_SENDER_EMAIL` | From address (verified domain) |
| `ADMIN_EMAIL` | Order + contact admin recipient |
| `EMAIL_ENABLED` | Kill switch |
| `EMAIL_MAX_RETRIES` | Retry budget |

## Queue-ready

`EmailQueue` protocol + `InProcessEmailQueue` today. Swap for Celery/RQ later without changing endpoints.
