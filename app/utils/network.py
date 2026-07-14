"""Client IP and network helpers for rate limiting and security events."""

from __future__ import annotations

from starlette.requests import Request

from app.config.settings import Settings


def get_client_ip(request: Request, settings: Settings | None = None) -> str:
    """
    Resolve the best-effort client IP.

    Forwarded headers (``X-Forwarded-For`` / ``X-Real-IP``) are honored only when
    ``TRUST_X_FORWARDED_FOR`` is enabled **and** the immediate peer is in
    ``TRUSTED_PROXY_IPS``. Otherwise the direct socket peer is used to prevent
    spoofing when the API is reachable without a stripping reverse proxy.
    """
    peer = request.client.host if request.client and request.client.host else "unknown"
    resolved = settings or getattr(getattr(request, "app", None), "state", None)
    cfg: Settings | None = None
    if isinstance(resolved, Settings):
        cfg = resolved
    else:
        cfg = getattr(resolved, "settings", None) if resolved is not None else None

    if cfg is None or not cfg.trust_x_forwarded_for:
        return peer

    trusted = set(cfg.trusted_proxy_ips)
    if peer not in trusted and "*" not in trusted:
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    return peer
