"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Capsule Cloud API"
    environment: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production-use-32-random-bytes"

    # Database
    database_url: str = "sqlite:///./capsule_cloud.db"

    # Object storage (Cloudflare R2 / S3-compatible)
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "capsule-sessions"

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Upload limits (bytes)
    max_upload_size_hobby: int = 100 * 1024 * 1024    # 100 MB
    max_upload_size_pro: int = 500 * 1024 * 1024      # 500 MB
    max_upload_size_business: int = 5 * 1024 * 1024 * 1024  # 5 GB

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "https://capsule.dev"]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
