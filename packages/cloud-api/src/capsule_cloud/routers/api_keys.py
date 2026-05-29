"""API key management endpoints — create, list, revoke."""

from __future__ import annotations

from datetime import datetime, timezone

import ulid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import generate_api_key, get_current_user, get_workspace_member
from capsule_cloud.database import get_db
from capsule_cloud.models import ApiKey, User
from capsule_cloud.schemas import ApiKeyResponse, CreateApiKeyRequest

router = APIRouter(prefix="/workspaces/{workspace_id}/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    workspace_id: str,
    body: CreateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """Create a new API key for the workspace. The full key is only returned once."""
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])

    full_key, key_prefix, key_hash = generate_api_key()

    api_key = ApiKey(
        id=str(ulid.new()),
        workspace_id=workspace_id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by_id=current_user.id,
        expires_at=body.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        workspace_id=api_key.workspace_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        full_key=full_key,  # Only returned on creation!
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    """List all active API keys for the workspace."""
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])

    result = await db.execute(
        select(ApiKey)
        .where(
            ApiKey.workspace_id == workspace_id,
            ApiKey.revoked_at.is_(None),
        )
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            workspace_id=k.workspace_id,
            name=k.name,
            key_prefix=k.key_prefix,
            created_at=k.created_at,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            full_key=None,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    workspace_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke (soft-delete) an API key."""
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.workspace_id == workspace_id,
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalars().first()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
