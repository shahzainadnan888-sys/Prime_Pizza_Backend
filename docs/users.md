# User Management Module

Production user profile, addresses, preferences, notifications, avatar upload, and
`users.json` synchronization for Prime Pizza.

## Architecture

```
API (/api/v1/users)
  → Dependencies (require_verified)
  → Services (Profile, User, Address, Avatar, Preference, Notification, Sync)
  → Repositories (User, Address, Preference, Notification)
  → PostgreSQL (source of truth)
  → UsersJsonMirror (best-effort dual-write to data/users.json)
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/users/me` | Own profile |
| PATCH | `/users/me` | Update name / email |
| POST | `/users/avatar` | Upload avatar (Cloudinary) |
| DELETE | `/users/avatar` | Remove avatar |
| POST | `/users/me/deactivate` | Deactivate account |
| DELETE | `/users/me` | Soft-delete account |
| GET/POST | `/users/addresses` | List / create |
| PATCH/DELETE | `/users/addresses/{id}` | Update / delete |
| PATCH | `/users/addresses/{id}/default` | Set default |
| GET/PATCH | `/users/preferences` | Preferences |
| GET | `/users/notifications` | Inbox |
| PATCH | `/users/notifications/read-all` | Mark all read |
| PATCH | `/users/notifications/{id}/read` | Mark one read |
| DELETE | `/users/notifications/{id}` | Soft-delete |

Owner admin user APIs are intentionally not exposed yet. Repository search helpers
(`search`, `search_by_phone`, `search_by_email`, `search_by_name`) are ready.

## Security

- All routes require a verified authenticated user.
- Address / notification lookups are scoped by `user_id` (404 on foreign IDs).
- Avatar uploads validate size, content-type, extension, and magic bytes.
- Only Cloudinary URL + `public_id` are stored (no binary in Postgres).

## Configuration

See `.env.example`:

- `MAX_ADDRESSES_PER_USER` (default 10)
- `AVATAR_MAX_BYTES` (default 5MB)
- `AVATAR_ALLOWED_CONTENT_TYPES`
