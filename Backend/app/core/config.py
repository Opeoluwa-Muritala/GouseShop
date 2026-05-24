from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GouseShop Backend"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./gouseshop.db"
    redis_url: str = "redis://localhost:6379/0"
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
    payment_callback_url: str = "http://localhost:3000/payment/callback"

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_folder: str = "gouseshop"

    resend_api_key: str | None = None
    email_from: str = "GouseShop <no-reply@gouseshop.local>"
    email_reply_to: str | None = None


settings = Settings()
