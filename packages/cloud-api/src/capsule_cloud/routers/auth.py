"""Auth endpoints — signup, login, refresh, logout."""

# NOTE: intentionally no `from __future__ import annotations` here — slowapi's
# @limiter.limit(...) wraps each endpoint in a function defined in slowapi's
# own module, whose __globals__ (not __module__) is what typing.get_type_hints
# uses to resolve string/forward-ref annotations. Under postponed evaluation
# every annotation becomes a string, so FastAPI/Pydantic can't find e.g.
# "SignupRequest" via that wrapper's globals and raises
# PydanticUndefinedAnnotation. Python 3.11 (this project's floor) supports
# `X | None` natively, so the future-import isn't needed for that syntax here.

from datetime import timedelta

import anyio.to_thread
import ulid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import (
    _create_token,
    _decode_token_payload,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh,
    hash_password,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    verify_password,
)
from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud.models import User, Workspace, WorkspaceMember
from capsule_cloud.rate_limit import limiter
from capsule_cloud.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory set of consumed password-reset JTIs.
# Prevents a reset link from being replayed within its 1-hour window.
# NOTE: This is per-process. Multi-worker deployments should replace this
#       with a shared store (Redis SETEX, or a DB-backed blocklist table).
_used_reset_jtis: set[str] = set()


@router.post(
    "/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("3/minute")
async def signup(
    request: Request, body: SignupRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Create a new user account and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user_id = str(ulid.new())
    hashed_password = await anyio.to_thread.run_sync(hash_password, body.password)
    user = User(
        id=user_id,
        email=str(body.email),
        full_name=body.full_name,
        hashed_password=hashed_password,
    )
    db.add(user)

    # Create a default personal workspace for the new user
    ws_id = str(ulid.new())
    slug_base = (
        str(body.email).split("@")[0].lower().replace(".", "-").replace("_", "-")
    )
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
@limiter.limit("5/minute")
async def login(
    request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
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
    valid = await anyio.to_thread.run_sync(
        verify_password, body.password, user.hashed_password
    )
    if not valid:
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
            select(User).where(
                User.email == str(body.email), User.id != current_user.id
            )
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
    valid = await anyio.to_thread.run_sync(
        verify_password, body.current_password, current_user.hashed_password
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = await anyio.to_thread.run_sync(
        hash_password, body.new_password
    )
    # A password change should evict anyone else holding a valid refresh
    # token for this account (e.g. an attacker with a stolen token) — not
    # just future requests using the current session's own tokens.
    revoke_all_refresh_tokens(current_user)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    body: LogoutRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout — revokes the given refresh token so it can't mint new access
    tokens again. Without one, this is still a 200 (matches the previous
    fully-stateless behavior) but there's nothing to revoke."""
    if body and body.refresh_token:
        await revoke_refresh_token(body.refresh_token, db)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate a password-reset token.

    Always returns the same generic message regardless of whether the account
    exists (avoids user enumeration) or which environment is running — the
    token is never echoed in the HTTP response. In development it is logged
    to the console instead so the flow is testable without email.
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

        if settings.resend_api_key:
            import httpx

            reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
            html_content = f"""
            <p>Hi,</p>
            <p>Someone requested a password reset for your Capsule account.</p>
            <p><a href="{reset_url}">Click here to reset your password</a></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            """
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                        json={
                            "from": settings.resend_from_email,
                            "to": str(body.email),
                            "subject": "Reset your Capsule password",
                            "html": html_content,
                        },
                        timeout=5.0,
                    )
                    response.raise_for_status()
                logger.info("password_reset.email_sent", email=str(body.email))
            except Exception as e:
                # If we get an error response, try to log the body too
                err_msg = str(e)
                if (
                    hasattr(e, "response")
                    and e.response is not None
                    and hasattr(e.response, "text")
                ):
                    err_msg += f" - {e.response.text}"
                logger.error(
                    "password_reset.email_failed", email=str(body.email), error=err_msg
                )

        if settings.environment == "development":
            # Never echo the token in the response — log it so the flow is
            # testable locally without needing a real email provider.
            logger.info(
                "password_reset.dev_token",
                email=str(body.email),
                reset_token=reset_token,
            )

    return {
        "message": "If an account exists with that email, you'll receive a reset link shortly."
    }


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
        raise _bad_token from None

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

    user.hashed_password = await anyio.to_thread.run_sync(
        hash_password, body.new_password
    )
    # Otherwise an attacker's stolen refresh token would keep minting access
    # tokens for up to 30 days after the victim "recovered" their account.
    revoke_all_refresh_tokens(user)
    await db.commit()
    return {"message": "Password updated successfully. You can now log in."}
