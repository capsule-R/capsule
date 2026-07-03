"""Authentication utilities — JWT (EdDSA/Ed25519) and API key management."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt as pyjwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    full_key   = 'csk_' + 48 url-safe random bytes (~64 chars)
    key_prefix = first 12 chars (display only)
    key_hash   = SHA-256 hex of the full key (stored in DB)
    """
    raw = secrets.token_urlsafe(48)
    full_key = f"csk_{raw}"
    key_prefix = full_key[:12]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, key_hash


def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()


# ── JWT (EdDSA / Ed25519) ─────────────────────────────────────
#
# We use asymmetric EdDSA so:
#   • Only the backend (holding the private key) can ISSUE tokens.
#   • Any service holding only the public key can VERIFY tokens.
#   • A leaked public key is harmless; a leaked secret_key (HS256) would
#     compromise every token ever issued.

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _get_private_key():
    """Load the Ed25519 private key object (cached via get_settings singleton)."""
    settings = get_settings()
    return load_pem_private_key(settings.jwt_private_key.encode(), password=None)


def _get_public_key():
    """Load the Ed25519 public key object (cached via get_settings singleton)."""
    settings = get_settings()
    return load_pem_public_key(settings.jwt_public_key.encode())


def _create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    payload = dict(data)
    now = datetime.now(timezone.utc)
    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "type": token_type,
            "jti": str(uuid.uuid4()),  # unique ID enabling per-token revocation
        }
    )
    return pyjwt.encode(payload, _get_private_key(), algorithm="EdDSA")


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


def _decode_token_payload(token: str, expected_type: str) -> dict[str, Any]:
    """Decode an EdDSA JWT and return the full validated payload."""
    try:
        payload = pyjwt.decode(
            token,
            _get_public_key(),
            algorithms=["EdDSA"],
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )
    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return payload


def _decode_token(token: str, expected_type: str) -> str:
    """Decode an EdDSA JWT and return the user_id (sub claim)."""
    return _decode_token_payload(token, expected_type)["sub"]


# ── FastAPI dependencies ──────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate request via JWT Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_token(credentials.credentials, _ACCESS_TOKEN_TYPE)
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_from_refresh(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate request via Refresh token (for the /auth/refresh endpoint)."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = _decode_token(credentials.credentials, _REFRESH_TOKEN_TYPE)
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_workspace_member(
    workspace_id: str,
    current_user: User,
    db: AsyncSession,
    required_roles: list[str] | None = None,
) -> WorkspaceMember:
    """Return the WorkspaceMember row; raises 403/404 if not found or wrong role."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if required_roles and member.role not in required_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return member


async def authenticate_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, ApiKey]:
    """Authenticate via API key. Returns (user, api_key) tuple.

    Callers that scope a request to a specific workspace_id (i.e. every
    session/workspace route) MUST also verify ``api_key.workspace_id`` matches
    that workspace — see get_current_principal. Without that check, a key
    minted for one workspace would authenticate as the key owner's full User,
    who may belong to (and could then act on) other workspaces too.
    """
    if credentials is None or not credentials.credentials.startswith("csk_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    key_hash = hash_api_key(credentials.credentials)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
            (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > now),
        )
    )
    api_key = result.scalars().first()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key")
    api_key.last_used_at = now
    await db.commit()

    from capsule_cloud.models import Workspace
    ws_result = await db.execute(
        select(Workspace).where(
            Workspace.id == api_key.workspace_id, Workspace.deleted_at.is_(None)
        )
    )
    workspace = ws_result.scalars().first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key workspace not found")

    user_result = await db.execute(
        select(User).where(User.id == workspace.owner_id, User.deleted_at.is_(None))
    )
    user = user_result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key owner not found")
    return user, api_key


async def get_current_principal(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate a workspace-scoped request via EITHER a JWT access token
    OR a ``csk_...`` API key.

    ``workspace_id`` is bound from the route's own path parameter (FastAPI
    resolves sub-dependency parameters the same way it resolves endpoint
    parameters). When authenticating via API key, the key's workspace_id must
    match the workspace being accessed — otherwise a key minted for workspace
    A could be used to act as its owner in workspace B too, since the key
    resolves to the owner's full User account.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials.startswith("csk_"):
        user, api_key = await authenticate_api_key(credentials, db)
        if api_key.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This API key is not authorized for this workspace",
            )
        return user

    user_id = _decode_token(credentials.credentials, _ACCESS_TOKEN_TYPE)
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
