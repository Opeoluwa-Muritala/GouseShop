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
    use_fake_external_services: bool = True

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
                return value
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def allowed_cors_origins(self) -> list[str]:
        return sorted(set(self.cors_origins))

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
