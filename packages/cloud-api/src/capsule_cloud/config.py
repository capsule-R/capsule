"""Application configuration via environment variables."""

from __future__ import annotations

import warnings
from typing import ClassVar

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Capsule Cloud API"

    # [REQUIRED] No default on purpose: defaulting to "development" here previously
    # meant an operator who forgot to set ENVIRONMENT in production silently got
    # dev-mode behavior (password-reset tokens echoed in API responses, Swagger
    # docs exposed, etc.) — a fail-open trap. Now a missing/invalid value raises
    # at startup instead of silently degrading security.
    environment: str
    debug: bool = False

    _VALID_ENVIRONMENTS: ClassVar[set[str]] = {"development", "staging", "production"}

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in cls._VALID_ENVIRONMENTS:
            raise ValueError(
                f"ENVIRONMENT must be one of {sorted(cls._VALID_ENVIRONMENTS)}, got {v!r}. "
                "Set it explicitly — there is no default."
            )
        return v

    # Kept for non-JWT HMAC uses (e.g. signed URLs, CSRF).
    # NOT used for JWT signing — EdDSA keypair below is used for that.
    secret_key: str = "change-me-in-production-use-32-random-bytes"

    # Database
    database_url: str = "sqlite+aiosqlite:///./capsule_cloud.db"
    # Publicly reachable DB URL for out-of-network workers (e.g. the Modal
    # replay worker) to write results back. On Railway, database_url is the
    # INTERNAL host (postgres.railway.internal) which Modal cannot reach, so
    # the worker's status write-back silently fails and replays stay "queued".
    # Set DATABASE_URL_DIRECT to the public/proxy URL (same one Alembic uses).
    # Falls back to database_url when unset (fine for local/dev).
    database_url_direct: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_async_database_url(cls, v: str) -> str:
        """Normalise database URLs for async SQLAlchemy drivers.

        Handles:
          postgres://       (Heroku/Railway shorthand)
          postgresql://     (standard, needs +asyncpg)
          sqlite:///        (needs +aiosqlite)
          unresolved Railway template variables  → clear error
          empty string                           → clear error
        """
        v = (v or "").strip()

        # Railway template variable was never resolved — "${{Postgres.DATABASE_URL}}"
        if v.startswith("${{") or v.startswith("${"):
            raise ValueError(
                "DATABASE_URL looks like an unresolved Railway template variable "
                f"({v!r}). "
                "Go to Railway → your service → Variables and make sure "
                "DATABASE_URL is linked to your PostgreSQL service "
                "(click 'Add Reference' and select the Postgres DATABASE_URL)."
            )

        if not v:
            raise ValueError(
                "DATABASE_URL is empty. "
                "In Railway: go to your service → Variables → "
                "add DATABASE_URL and reference your PostgreSQL plugin."
            )

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
    def normalize_pem(cls, v: str) -> str:
        """Make PEM keys robust to however they were pasted into an env var.

        Handles the common ways a multi-line PEM gets mangled in a hosting
        dashboard (Railway/Vercel/etc.):
          • surrounding quotes
          • literal ``\\n`` / ``\\r\\n`` escapes instead of real newlines
          • the whole PEM base64-encoded into one token
          • the PEM flattened onto a single line (framing + body run together)

        The body is re-wrapped at 64 chars and the BEGIN/END framing is rebuilt,
        which fixes the ``MalformedFraming`` error from python-cryptography.
        """
        if not v:
            return v
        s = v.strip()

        # 1) Strip accidental surrounding quotes.
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
            s = s[1:-1].strip()

        # 2) Turn literal escape sequences into real newlines.
        s = s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")

        # 3) If there's no PEM header, maybe the whole PEM was base64-encoded.
        if "-----BEGIN" not in s:
            import base64
            try:
                decoded = base64.b64decode(s, validate=False).decode()
                if "-----BEGIN" in decoded:
                    s = decoded.strip()
            except Exception:
                pass

        # 4) Rebuild framing if header/body/footer got flattened together.
        return cls._reframe_pem(s)

    @staticmethod
    def _reframe_pem(s: str) -> str:
        import re

        m = re.search(
            r"-----BEGIN ([A-Z0-9 ]+?)-----(.*?)-----END \1-----",
            s,
            re.DOTALL,
        )
        if not m:
            return s
        label = m.group(1).strip()
        body = re.sub(r"\s+", "", m.group(2))  # strip ALL whitespace from body
        wrapped = "\n".join(body[i : i + 64] for i in range(0, len(body), 64))
        return f"-----BEGIN {label}-----\n{wrapped}\n-----END {label}-----\n"

    @model_validator(mode="after")
    def ensure_secret_key(self) -> "Settings":
        """Reject the well-known default secret_key in non-development environments."""
        default = "change-me-in-production-use-32-random-bytes"
        if self.secret_key == default and self.environment != "development":
            raise ValueError(
                "SECRET_KEY must be changed from the default in production. "
                "Set SECRET_KEY to a cryptographically random 32+ byte string."
            )
        return self

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

    # Email (Resend)
    resend_api_key: str = ""
    resend_from_email: str = "Capsule <onboarding@resend.dev>"
    frontend_url: str = "http://localhost:3000"

    # CORS — plain str so pydantic-settings never tries to json.loads() it.
    # Accepts comma-separated origins or a JSON array string.
    # Wildcards like https://*.vercel.app allow ANY app on that platform —
    # set ALLOWED_ORIGINS explicitly in production with only your own domains.
    allowed_origins: str = (
        "http://localhost:3000,"
        "https://capsule-five-delta.vercel.app"
    )

    def get_cors_origins(self) -> list[str]:
        """Parse allowed_origins into a list (raw, may contain wildcards)."""
        v = (self.allowed_origins or "").strip()
        if not v:
            return [
                "http://localhost:3000",
                "https://capsule-five-delta.vercel.app",
            ]
        if v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    def get_cors_config(self) -> dict:
        """Build kwargs for CORSMiddleware.

        FastAPI's CORSMiddleware does EXACT-string matching on allow_origins —
        it does NOT expand wildcards like ``https://*.vercel.app``. Any origin
        containing a ``*`` is therefore compiled into ``allow_origin_regex``
        instead, so deploy-preview / subdomain URLs actually match.
        """
        import re

        exact: list[str] = []
        regexes: list[str] = []
        for origin in self.get_cors_origins():
            if "*" in origin:
                # Escape everything, then turn the escaped \* back into .*
                pattern = re.escape(origin).replace(r"\*", r"[^.]+")
                regexes.append(pattern)
            else:
                exact.append(origin)

        cfg: dict = {"allow_origins": exact}
        if regexes:
            cfg["allow_origin_regex"] = "^(" + "|".join(regexes) + ")$"
        return cfg


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        # environment has no default on purpose (see the field above) — it is
        # sourced from the ENVIRONMENT env var at runtime, which mypy can't
        # see through BaseSettings' constructor signature.
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
