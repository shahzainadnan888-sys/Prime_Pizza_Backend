# Authentication

Phone-only authentication via **local Redis OTP** + JWT.

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/send-otp` | Public |
| POST | `/api/v1/auth/verify-otp` | Public |
| POST | `/api/v1/auth/refresh` | Public (refresh token body) |
| POST | `/api/v1/auth/logout` | Bearer |
| GET | `/api/v1/auth/me` | Bearer |

## Flow

1. Client sends E.164 phone to `send-otp`
2. `LocalOTPProvider` generates a 6-digit code (`secrets`)
3. Code stored at Redis key `otp:{phone}` (TTL `OTP_EXPIRE_SECONDS`, default 300)
4. OTP printed to the server terminal; echoed in JSON **only when** `APP_ENV=development`
5. Client submits code to `verify-otp`
6. On success: OTP deleted, user created/loaded in PostgreSQL, mirrored to `users.json`, JWT pair issued

## Services

1. Phone validation
2. Local OTP provider (swappable protocol for future Twilio/Firebase)
3. Redis OTP / rate-limit / refresh repositories
4. JWT service
5. Role assignment (`OWNER_PHONE_NUMBER` → owner)
6. User sync (`users.json`)

## Redis keys

| Key | Purpose |
|-----|---------|
| `otp:{phone}` | OTP session (code, timestamps, failed_attempts) |
| `auth:rate:*` | Send/verify rate limits |
| `auth:refresh:{jti}` | Refresh token store |
| `auth:blacklist:{jti}` | Revoked access/refresh JTIs |

## Owner

`OWNER_PHONE_NUMBER=+923348957141` logs in as `role=owner`. All other phones are `customer`.
