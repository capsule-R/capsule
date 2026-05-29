"""Application configuration via environment variables."""

from __future__ import annotations

import warnings

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Capsule Cloud API"
    environment: str = "development"
    debug: bool = False

    # Kept for non-JWT HMAC uses (e.g. signed URLs, CSRF).
    # NOT used for JWT signing — EdDSA keypair below is used for that.
    secret_key: str = "change-me-in-production-use-32-random-bytes"

    # Database
    database_url: str = "sqlite+aiosqlite:///./capsule_cloud.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_async_database_url(cls, v: str) -> str:
        """Auto-prefix legacy sync URLs so async SQLAlchemy drivers are used."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("sqlite:///") and "+aiosqlite" not in v:
            return v.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return v

    # JWT — EdDSA Ed25519 keypair
    # Store PEM strings; use \\n (literal backslash-n) in env vars and the
    # validator below converts them to real newlines.
    # To generate a keypair:
    #   python -c "
    #   from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    #   from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
    #   k = Ed25519PrivateKey.generate()
    #   print('PRIVATE:', k.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode().replace(chr(10), r'\n'))
    #   print('PUBLIC: ', k.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode().replace(chr(10), r'\n'))
    #   "
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "EdDSA"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    @field_validator("jwt_private_key", "jwt_public_key", mode="before")
    @classmethod
    def unescape_pem_newlines(cls, v: str) -> str:
        """Allow \\n literal in env vars to represent real newlines inside PEM blocks."""
        if v:
            return v.replace("\\n", "\n")
        return v

    @model_validator(mode="after")
    def ensure_jwt_keypair(self) -> "Settings":
        """Auto-generate ephemeral Ed25519 keys in development if none are configured."""
        if not self.jwt_private_key or not self.jwt_public_key:
            if self.environment != "development":
                raise ValueError(
                    "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be set in production. "
                    "Generate them with the command in config.py."
                )
            warnings.warn(
                "⚠️  No JWT keypair set — generating ephemeral Ed25519 keys. "
                "All tokens are invalidated on restart. "
                "Set JWT_PRIVATE_KEY + JWT_PUBLIC_KEY in .env for persistence.",
                stacklevel=2,
            )
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import (
                Encoding, NoEncryption, PrivateFormat, PublicFormat,
            )
            priv = Ed25519PrivateKey.generate()
            self.jwt_private_key = priv.private_bytes(
                Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
            ).decode()
            self.jwt_public_key = priv.public_key().public_bytes(
                Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
            ).decode()
        return self

    # Object storage (Backblaze B2 / Cloudflare R2 / any S3-compatible)
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "capsule-sessions"

    # Modal cloud replay
    modal_token_id: str = ""
    modal_token_secret: str = ""

    # Upload limits (bytes)
    max_upload_size_hobby: int = 100 * 1024 * 1024
    max_upload_size_pro: int = 500 * 1024 * 1024
    max_upload_size_business: int = 5 * 1024 * 1024 * 1024

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "https://capsule.dev",
        "https://*.vercel.app",
        "https://*.railway.app",
    ]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
