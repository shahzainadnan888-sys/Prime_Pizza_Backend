"""Centralized application configuration via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import AliasChoices, EmailStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration loaded from environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Prime Pizza API", alias="APP_NAME")
    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # Security
    secret_key: str = Field(..., min_length=32, alias="SECRET_KEY")
    algorithm: Literal["HS256"] = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    # Only honor X-Forwarded-For / X-Real-IP when the peer is a trusted proxy.
    trust_x_forwarded_for: bool = Field(default=False, alias="TRUST_X_FORWARDED_FOR")
    trusted_proxy_ips: list[str] = Field(
        default_factory=list,
        alias="TRUSTED_PROXY_IPS",
    )

    # OTP / rate limiting
    # OTP / rate limiting (local Redis OTP; remote providers plug in later)
    otp_expire_seconds: int = Field(
        default=300,
        ge=60,
        le=1800,
        validation_alias=AliasChoices("OTP_EXPIRE_SECONDS", "OTP_EXPIRY_SECONDS"),
    )
    otp_max_attempts: int = Field(default=5, ge=1, le=20, alias="OTP_MAX_ATTEMPTS")
    otp_send_limit: int = Field(default=3, ge=1, alias="OTP_SEND_LIMIT")
    otp_send_window_seconds: int = Field(
        default=600,
        ge=60,
        alias="OTP_SEND_WINDOW_SECONDS",
    )
    otp_verify_limit: int = Field(default=10, ge=1, alias="OTP_VERIFY_LIMIT")
    otp_verify_window_seconds: int = Field(
        default=600,
        ge=60,
        alias="OTP_VERIFY_WINDOW_SECONDS",
    )
    otp_ip_send_limit: int = Field(default=10, ge=1, alias="OTP_IP_SEND_LIMIT")
    otp_ip_send_window_seconds: int = Field(
        default=600,
        ge=60,
        alias="OTP_IP_SEND_WINDOW_SECONDS",
    )
    otp_ip_verify_limit: int = Field(default=30, ge=1, alias="OTP_IP_VERIFY_LIMIT")
    otp_ip_verify_window_seconds: int = Field(
        default=600,
        ge=60,
        alias="OTP_IP_VERIFY_WINDOW_SECONDS",
    )
    otp_global_send_limit: int = Field(default=200, ge=1, alias="OTP_GLOBAL_SEND_LIMIT")
    otp_global_send_window_seconds: int = Field(
        default=3600,
        ge=60,
        alias="OTP_GLOBAL_SEND_WINDOW_SECONDS",
    )

    # HTTP rate limiting (Redis)
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_owner_bypass: bool = Field(default=False, alias="RATE_LIMIT_OWNER_BYPASS")
    rate_limit_bypass_ips: list[str] = Field(
        default_factory=list,
        alias="RATE_LIMIT_BYPASS_IPS",
    )
    rate_limit_fail_closed_policies: list[str] = Field(
        default_factory=lambda: ["auth", "upload", "email", "orders"],
        alias="RATE_LIMIT_FAIL_CLOSED_POLICIES",
    )
    rate_limit_checkout_per_minute: int = Field(
        default=30,
        ge=1,
        alias="RATE_LIMIT_CHECKOUT_PER_MINUTE",
    )
    rate_limit_checkout_per_hour: int = Field(
        default=300,
        ge=1,
        alias="RATE_LIMIT_CHECKOUT_PER_HOUR",
    )
    rate_limit_checkout_burst: int = Field(
        default=12,
        ge=1,
        alias="RATE_LIMIT_CHECKOUT_BURST",
    )
    rate_limit_default_per_minute: int = Field(default=120, ge=1, alias="RATE_LIMIT_DEFAULT_PER_MINUTE")
    rate_limit_default_per_hour: int = Field(default=3000, ge=1, alias="RATE_LIMIT_DEFAULT_PER_HOUR")
    rate_limit_default_burst: int = Field(default=40, ge=1, alias="RATE_LIMIT_DEFAULT_BURST")
    rate_limit_auth_per_minute: int = Field(default=20, ge=1, alias="RATE_LIMIT_AUTH_PER_MINUTE")
    rate_limit_auth_per_hour: int = Field(default=120, ge=1, alias="RATE_LIMIT_AUTH_PER_HOUR")
    rate_limit_auth_burst: int = Field(default=10, ge=1, alias="RATE_LIMIT_AUTH_BURST")
    rate_limit_orders_per_minute: int = Field(default=15, ge=1, alias="RATE_LIMIT_ORDERS_PER_MINUTE")
    rate_limit_orders_per_hour: int = Field(default=100, ge=1, alias="RATE_LIMIT_ORDERS_PER_HOUR")
    rate_limit_orders_burst: int = Field(default=8, ge=1, alias="RATE_LIMIT_ORDERS_BURST")
    rate_limit_search_per_minute: int = Field(default=60, ge=1, alias="RATE_LIMIT_SEARCH_PER_MINUTE")
    rate_limit_search_per_hour: int = Field(default=1000, ge=1, alias="RATE_LIMIT_SEARCH_PER_HOUR")
    rate_limit_search_burst: int = Field(default=25, ge=1, alias="RATE_LIMIT_SEARCH_BURST")
    rate_limit_admin_per_minute: int = Field(default=90, ge=1, alias="RATE_LIMIT_ADMIN_PER_MINUTE")
    rate_limit_admin_per_hour: int = Field(default=2000, ge=1, alias="RATE_LIMIT_ADMIN_PER_HOUR")
    rate_limit_admin_burst: int = Field(default=30, ge=1, alias="RATE_LIMIT_ADMIN_BURST")
    rate_limit_upload_per_minute: int = Field(default=20, ge=1, alias="RATE_LIMIT_UPLOAD_PER_MINUTE")
    rate_limit_upload_per_hour: int = Field(default=200, ge=1, alias="RATE_LIMIT_UPLOAD_PER_HOUR")
    rate_limit_upload_burst: int = Field(default=8, ge=1, alias="RATE_LIMIT_UPLOAD_BURST")
    rate_limit_email_per_minute: int = Field(default=10, ge=1, alias="RATE_LIMIT_EMAIL_PER_MINUTE")
    rate_limit_email_per_hour: int = Field(default=60, ge=1, alias="RATE_LIMIT_EMAIL_PER_HOUR")
    rate_limit_email_burst: int = Field(default=5, ge=1, alias="RATE_LIMIT_EMAIL_BURST")
    rate_limit_health_per_minute: int = Field(default=180, ge=1, alias="RATE_LIMIT_HEALTH_PER_MINUTE")
    rate_limit_health_per_hour: int = Field(default=5000, ge=1, alias="RATE_LIMIT_HEALTH_PER_HOUR")
    rate_limit_health_burst: int = Field(default=60, ge=1, alias="RATE_LIMIT_HEALTH_BURST")

    # OpenAPI documentation exposure
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")

    # Request body / upload safety
    max_request_body_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        alias="MAX_REQUEST_BODY_BYTES",
    )

    # Database pool
    db_pool_size: int = Field(default=5, ge=1, le=50, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, ge=0, le=50, alias="DB_MAX_OVERFLOW")
    db_pool_recycle_seconds: int = Field(default=1800, ge=60, alias="DB_POOL_RECYCLE_SECONDS")
    db_pool_timeout_seconds: int = Field(default=30, ge=1, alias="DB_POOL_TIMEOUT_SECONDS")

    # Redis client
    redis_max_connections: int = Field(default=20, ge=1, le=200, alias="REDIS_MAX_CONNECTIONS")

    # Security headers
    enable_hsts: bool = Field(default=False, alias="ENABLE_HSTS")
    hsts_max_age_seconds: int = Field(default=31_536_000, ge=60, alias="HSTS_MAX_AGE_SECONDS")
    enable_csp: bool = Field(default=True, alias="ENABLE_CSP")
    content_security_policy: str = Field(
        default="default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        alias="CONTENT_SECURITY_POLICY",
    )

    # User module
    max_addresses_per_user: int = Field(default=10, ge=1, le=50, alias="MAX_ADDRESSES_PER_USER")
    avatar_max_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1024,
        alias="AVATAR_MAX_BYTES",
    )
    avatar_allowed_content_types: list[str] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        ],
        alias="AVATAR_ALLOWED_CONTENT_TYPES",
    )

    # Catalog / product module
    max_product_images: int = Field(default=10, ge=1, le=30, alias="MAX_PRODUCT_IMAGES")
    product_image_max_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1024,
        alias="PRODUCT_IMAGE_MAX_BYTES",
    )
    catalog_cache_ttl_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        alias="CATALOG_CACHE_TTL_SECONDS",
    )

    # Orders
    order_cache_ttl_seconds: int = Field(
        default=120,
        ge=30,
        le=1800,
        alias="ORDER_CACHE_TTL_SECONDS",
    )
    checkout_lock_ttl_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        alias="CHECKOUT_LOCK_TTL_SECONDS",
    )
    order_cancel_window_minutes: int = Field(
        default=15,
        ge=1,
        le=240,
        alias="ORDER_CANCEL_WINDOW_MINUTES",
    )

    # Cart / checkout preparation
    cart_cache_ttl_seconds: int = Field(
        default=120,
        ge=30,
        le=1800,
        alias="CART_CACHE_TTL_SECONDS",
    )
    cart_min_item_quantity: int = Field(default=1, ge=1, alias="CART_MIN_ITEM_QUANTITY")
    cart_max_item_quantity: int = Field(default=20, ge=1, le=100, alias="CART_MAX_ITEM_QUANTITY")
    cart_max_items: int = Field(default=50, ge=1, le=200, alias="CART_MAX_ITEMS")
    delivery_fee_flat: float = Field(default=150.0, ge=0, alias="DELIVERY_FEE_FLAT")
    free_delivery_threshold: float = Field(
        default=2000.0,
        ge=0,
        alias="FREE_DELIVERY_THRESHOLD",
    )
    tax_rate_percent: float = Field(default=0.0, ge=0, le=100, alias="TAX_RATE_PERCENT")
    estimated_prep_buffer_minutes: int = Field(
        default=15,
        ge=0,
        alias="ESTIMATED_PREP_BUFFER_MINUTES",
    )
    estimated_delivery_minutes: int = Field(
        default=45,
        ge=1,
        alias="ESTIMATED_DELIVERY_MINUTES",
    )

    # Owner dashboard / analytics
    dashboard_cache_ttl_seconds: int = Field(
        default=60,
        ge=15,
        le=1800,
        alias="DASHBOARD_CACHE_TTL_SECONDS",
    )

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(..., alias="REDIS_URL")

    # Cloudinary
    cloudinary_cloud_name: str = Field(..., alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(..., alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(..., alias="CLOUDINARY_API_SECRET")

    # Resend
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    resend_from_email: EmailStr | str = Field(
        default="noreply@primepizza.com",
        alias="RESEND_FROM_EMAIL",
    )
    # Optional brand assets (placeholders work when empty)
    email_logo_url: str = Field(default="", alias="EMAIL_LOGO_URL")
    email_brand_name: str = Field(default="Prime Pizza", alias="EMAIL_BRAND_NAME")
    email_max_retries: int = Field(default=3, ge=1, le=5, alias="EMAIL_MAX_RETRIES")
    email_retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=30.0,
        alias="EMAIL_RETRY_BACKOFF_SECONDS",
    )
    email_enabled: bool = Field(default=True, alias="EMAIL_ENABLED")
    # Comma-separated additional owners for future multi-recipient support
    owner_notification_emails: str = Field(default="", alias="OWNER_NOTIFICATION_EMAILS")

    # Owner contacts
    owner_phone_number: str = Field(..., alias="OWNER_PHONE_NUMBER")
    owner_email: EmailStr = Field(..., alias="OWNER_EMAIL")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, ge=1, le=65535, alias="PORT")
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"],
        alias="ALLOWED_HOSTS",
    )

    def owner_email_recipients(self) -> list[str]:
        """
        Recipients for new-order owner notifications.

        Always includes OWNER_EMAIL. Additional addresses may be supplied via
        OWNER_NOTIFICATION_EMAILS (comma-separated) without code changes.
        """
        recipients: list[str] = [str(self.owner_email).strip().lower()]
        extras = [
            part.strip().lower()
            for part in self.owner_notification_emails.split(",")
            if part.strip()
        ]
        for email in extras:
            if email not in recipients:
                recipients.append(email)
        return recipients

    @property
    def is_email_configured(self) -> bool:
        return bool(self.resend_api_key.strip()) and self.email_enabled

    @field_validator("api_v1_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        prefix = value.strip()
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix.rstrip("/") or "/api/v1"

    @field_validator("owner_phone_number")
    @classmethod
    def normalize_owner_phone(cls, value: str) -> str:
        from app.utils.phone import normalize_phone

        return normalize_phone(value)

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """
        Ensure SQLAlchemy async driver is used for PostgreSQL URLs.

        Neon pooler URLs often include libpq-only params (`sslmode`, `channel_binding`)
        that asyncpg does not accept — convert them to asyncpg-compatible form.
        """
        url = value.strip()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        ssl_required = query.pop("sslmode", None) in {"require", "verify-ca", "verify-full"}
        query.pop("channel_binding", None)
        if ssl_required and "ssl" not in query:
            query["ssl"] = "require"
        return urlunparse(parsed._replace(query=urlencode(query)))

    @field_validator("redis_url")
    @classmethod
    def normalize_redis_url(cls, value: str) -> str:
        """
        Accept raw Redis URLs and common CLI paste mistakes.

        Converts Upstash `redis-cli --tls -u redis://...` pastes into `rediss://...`.
        """
        url = value.strip()
        if "redis://" in url or "rediss://" in url:
            for marker in ("rediss://", "redis://"):
                idx = url.find(marker)
                if idx != -1:
                    url = url[idx:].split()[0]
                    break
            if "--tls" in value and url.startswith("redis://"):
                url = "rediss://" + url.removeprefix("redis://")
        return url

    @model_validator(mode="after")
    def validate_production_hardening(self) -> Settings:
        if self.app_env == "test":
            object.__setattr__(self, "rate_limit_enabled", False)
            return self

        if self.app_env != "production":
            return self

        errors: list[str] = []
        if self.debug:
            errors.append("DEBUG must be false when APP_ENV is production")
        if self.secret_key.lower().startswith("change-me"):
            errors.append("SECRET_KEY must not use the placeholder value in production")
        if len(self.secret_key) < 48:
            errors.append("SECRET_KEY should be at least 48 characters in production")
        if self.frontend_url.startswith("http://"):
            errors.append("FRONTEND_URL must use HTTPS in production")
        default_hosts = {"localhost", "127.0.0.1", "testserver"}
        if not self.allowed_hosts or set(self.allowed_hosts) <= default_hosts:
            errors.append("ALLOWED_HOSTS must be explicitly configured for production")
        if "*" in self.allowed_hosts:
            errors.append("ALLOWED_HOSTS must not contain '*' in production")
        if not self.redis_url.startswith("rediss://") and "localhost" not in self.redis_url:
            errors.append("REDIS_URL should use TLS (rediss://) in production")
        if self.algorithm != "HS256":
            errors.append("ALGORITHM must be HS256 in production")
        if self.trust_x_forwarded_for and not self.trusted_proxy_ips:
            errors.append(
                "TRUSTED_PROXY_IPS must be set when TRUST_X_FORWARDED_FOR is enabled in production"
            )
        if self.rate_limit_owner_bypass and not self.rate_limit_bypass_ips:
            errors.append(
                "RATE_LIMIT_BYPASS_IPS must be configured when RATE_LIMIT_OWNER_BYPASS is enabled"
            )
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @property
    def docs_enabled(self) -> bool:
        """OpenAPI / Swagger / ReDoc are never exposed in production."""
        if self.app_env == "production":
            return False
        return self.enable_docs

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]

    @property
    def sync_database_url(self) -> str:
        """Sync URL for tooling that prefers psycopg over asyncpg."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for dependency injection."""
    return Settings()
