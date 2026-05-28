"""Authentication utilities — JWT tokens and API key management."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud.models import ApiKey, User, WorkspaceMember

# ── Password hashing (Argon2id) ───────────────────────────────

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── API key generation and hashing ───────────────────────────

def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, key_prefix, key_hash).

    full_key  = 'csk_' + 48 url-safe random bytes (base64 ~ 64 chars)
    key_prefix = first 12 chars (for display)
    key_hash   = SHA-256 hex of the full key (stored in DB)
    """
    raw = secrets.token_urlsafe(48)
    full_key = f"csk_{raw}"
    key_prefix = full_key[:12]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, key_hash


def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()


# ── JWT ───────────────────────────────────────────────────────

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    settings = get_settings()
    payload = dict(data)
    now = datetime.now(timezone.utc)
    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "type": token_type,
        }
    )
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(
        {"sub": user_id},
        _ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(
        {"sub": user_id},
        _REFRESH_TOKEN_TYPE,
        timedelta(days=settings.refresh_token_expire_days),
    )


def _decode_token(token: str, expected_type: str) -> str:
    """Decode a JWT and return the user_id (sub claim)."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return user_id


# ── FastAPI dependencies ──────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: DBSession = Depends(get_db),
) -> User:
    """Authenticate request via JWT Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_token(credentials.credentials, _ACCESS_TOKEN_TYPE)
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_from_refresh(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: DBSession = Depends(get_db),
) -> User:
    """Authenticate request via Refresh token (for the /auth/refresh endpoint)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = _decode_token(credentials.credentials, _REFRESH_TOKEN_TYPE)
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_workspace_member(
    workspace_id: str,
    current_user: User,
    db: DBSession,
    required_roles: list[str] | None = None,
) -> WorkspaceMember:
    """Return the WorkspaceMember row; raises 403/404 if not found or wrong role."""
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if required_roles and member.role not in required_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return member


def authenticate_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: DBSession = Depends(get_db),
) -> tuple[User, ApiKey]:
    """Authenticate via API key. Returns (user, api_key) tuple."""
    if credentials is None or not credentials.credentials.startswith("csk_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    key_hash = hash_api_key(credentials.credentials)
    now = datetime.now(timezone.utc)
    api_key = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
            (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > now),
        )
        .first()
    )
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key")
    # update last_used_at
    api_key.last_used_at = now
    db.commit()
    workspace = api_key.workspace
    # Return the owner as the "user" for API key auth
    user = db.query(User).filter(User.id == workspace.owner_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key owner not found")
    return user, api_key
