from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GouseShop Backend"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./gouseshop.db"
    redis_url: str = "redis://localhost:6379/0"
    use_fake_redis: bool = True
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
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
    email_from: str = "GouseShop <no-reply@gouseshop.local>"
    email_reply_to: str | None = None

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


settings = Settings()
