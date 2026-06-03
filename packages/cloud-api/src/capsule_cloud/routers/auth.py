"""Auth endpoints — signup, login, refresh, logout."""

from __future__ import annotations

from datetime import timedelta

import ulid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import (
    _create_token,
    _decode_token,
    _decode_token_payload,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh,
    hash_password,
    verify_password,
)

# In-memory set of consumed password-reset JTIs.
# Prevents a reset link from being replayed within its 1-hour window.
# NOTE: This is per-process. Multi-worker deployments should replace this
#       with a shared store (Redis SETEX, or a DB-backed blocklist table).
_used_reset_jtis: set[str] = set()
from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud.models import User, Workspace, WorkspaceMember
from capsule_cloud.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new user account and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user_id = str(ulid.new())
    user = User(
        id=user_id,
        email=str(body.email),
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)

    # Create a default personal workspace for the new user
    ws_id = str(ulid.new())
    slug_base = str(body.email).split("@")[0].lower().replace(".", "-").replace("_", "-")
    # ensure slug uniqueness (append partial user id)
    slug = f"{slug_base}-{user_id[-6:].lower()}"
    workspace = Workspace(
        id=ws_id,
        name=f"{body.full_name or body.email}'s Workspace",
        slug=slug,
        owner_id=user_id,
    )
    db.add(workspace)

    # Add owner as a member
    member = WorkspaceMember(
        id=str(ulid.new()),
        workspace_id=ws_id,
        user_id=user_id,
        role="owner",
    )
    db.add(member)
    await db.commit()

    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate with email/password and return JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == str(body.email), User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user_from_refresh),
) -> TokenResponse:
    """Exchange a refresh token for a new access+refresh token pair."""
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(current_user.id),
        refresh_token=create_refresh_token(current_user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the current user's display name or email."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.email is not None:
        # Check uniqueness
        result = await db.execute(
            select(User).where(User.email == str(body.email), User.id != current_user.id)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        current_user.email = str(body.email)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change the current user's password (requires current password for verification)."""
    if current_user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses OAuth login and has no password to change",
        )
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout() -> dict:
    """Logout endpoint — client should clear its tokens. No server-side state to clear (stateless JWTs)."""
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate a password-reset token.

    In production this sends an email with the reset link.
    For development the reset token is returned in the response body.
    """
    import structlog as _log
    logger = _log.get_logger(__name__)

    # Always return the same message to avoid user enumeration
    result = await db.execute(
        select(User).where(User.email == str(body.email), User.deleted_at.is_(None))
    )
    user = result.scalars().first()

    if user:
        # Reuse the JWT machinery — create a short-lived password-reset token
        reset_token = _create_token(
            {"sub": user.id, "email": str(body.email)},
            "password_reset",
            timedelta(hours=1),
        )
        logger.info("password_reset.token_generated", email=str(body.email))
        settings = get_settings()
        if settings.environment == "development":
            # Return token directly in dev so the flow is testable without email
            return {
                "message": "Password reset token generated. In production this would be emailed.",
                "reset_token": reset_token,
            }

    return {"message": "If an account exists with that email, you'll receive a reset link shortly."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate a password-reset token and update the user's password."""
    _bad_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token",
    )
    # Decode and validate the JWT reset token, extracting full payload for jti check
    try:
        payload = _decode_token_payload(body.token, "password_reset")
        user_id: str = payload["sub"]
        jti: str | None = payload.get("jti")
    except HTTPException:
        raise _bad_token

    # Enforce single-use: reject if this token's jti has already been consumed
    if jti:
        if jti in _used_reset_jtis:
            raise _bad_token
        _used_reset_jtis.add(jti)

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None:
        raise _bad_token

    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password updated successfully. You can now log in."}
