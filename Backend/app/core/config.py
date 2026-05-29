import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GouseShop Backend"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./gouseshop.db"
    redis_url: str = "redis://localhost:6379/0"
    use_fake_redis: bool = True
    redis_key_prefix: str = "gouseshop:"
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30
    cors_origins: list[str] = Field(default_factory=list)
    cors_origin_regex: str | None = None
    allowed_hosts: list[str] = Field(default_factory=list)
    enable_api_docs: bool = False
    session_cookie_secure: bool | None = None
    session_cookie_samesite: str | None = None
    use_fake_external_services: bool = True

    admin_bootstrap_email: str | None = None
    admin_bootstrap_password: str | None = None

    paystack_secret_key: str | None = None
    paystack_public_key: str | None = None
    paystack_webhook_secret: str | None = None
    flutterwave_secret_key: str | None = None
    flutterwave_public_key: str | None = None
    flutterwave_webhook_secret: str | None = None
    flutterwave_client_id: str | None = None
    flutterwave_client_secret: str | None = None
    flw_client_id: str | None = None
    flw_client_secret: str | None = None
    payment_callback_url: str = "http://localhost:3000/payment/callback"

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_folder: str = "gouseshop"
    cloudinary_max_upload_bytes: int = 5 * 1024 * 1024

    resend_api_key: str | None = None
    email_api_url: str = "https://email-api-4ykn.onrender.com"
    email_from: str = "GouseShop <no-reply@gouseshop.local>"
    email_reply_to: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return json.loads(value)
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    @property
    def allowed_cors_origins(self) -> list[str]:
        origins = set(self.cors_origins)
        origins.update(
            {
                "https://gouseshop.onrender.com",
                "https://gouseshop-1.onrender.com",
            }
        )
        return sorted(origins)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.is_production

    @property
    def cookie_samesite(self) -> str:
        if self.session_cookie_samesite:
            return self.session_cookie_samesite.lower()
        return "none" if self.cookie_secure else "lax"

    @property
    def trusted_hosts(self) -> list[str]:
        hosts = set(self.allowed_hosts)
        if "*" in hosts:
            return ["*"]
        hosts.update({"localhost", "127.0.0.1", "testserver"})
        if self.is_production:
            hosts.update(
                {
                    "gouseshop.onrender.com",
                    "gouseshop-1.onrender.com",
                    "gouseshop-backend.onrender.com",
                    "*.onrender.com",
                }
            )
        return sorted(hosts)

    def validate_production_settings(self) -> None:
        if not self.is_production:
            return
        if self.jwt_secret in {"change-me", "change-me-in-production", "test-secret"} or len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be a strong production secret.")
        if self.cors_origin_regex and self.cors_origin_regex.strip() in {".*", "^.*$", "*"}:
            raise RuntimeError("CORS_ORIGIN_REGEX must not be permissive in production.")
        if self.admin_bootstrap_password and self.admin_bootstrap_password in {"Iamanadmin", "password", "admin"}:
            raise RuntimeError("ADMIN_BOOTSTRAP_PASSWORD must not use a default or weak value in production.")

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url
        if self.database_url.startswith("postgres://"):
            url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+asyncpg://"):
            parsed = urlsplit(url)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            sslmode = query.pop("sslmode", None)
            if sslmode and "ssl" not in query:
                query["ssl"] = "require" if sslmode == "require" else sslmode
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
        return url


settings = Settings()
