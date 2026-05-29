"""Auth endpoints — signup, login, refresh, logout."""

from __future__ import annotations

import ulid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh,
    hash_password,
    verify_password,
)
from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud.models import User, Workspace, WorkspaceMember
from capsule_cloud.schemas import LoginRequest, SignupRequest, TokenResponse, UserResponse

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
