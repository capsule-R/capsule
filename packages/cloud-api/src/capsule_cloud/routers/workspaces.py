"""Workspace CRUD and member management endpoints."""

from __future__ import annotations

import ulid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import get_current_user, get_workspace_member
from capsule_cloud.database import get_db
from capsule_cloud.models import User, Workspace, WorkspaceMember
from capsule_cloud.schemas import (
    CreateWorkspaceRequest,
    InviteMemberRequest,
    MemberResponse,
    UpdateWorkspaceRequest,
    WorkspaceResponse,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ── Workspace CRUD ────────────────────────────────────────────

@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Workspace]:
    """List all workspaces the authenticated user is a member of."""
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == current_user.id)
    )
    memberships = result.scalars().all()
    workspace_ids = [m.workspace_id for m in memberships]
    result = await db.execute(
        select(Workspace).where(Workspace.id.in_(workspace_ids), Workspace.deleted_at.is_(None))
    )
    return list(result.scalars().all())


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Create a new workspace owned by the current user."""
    result = await db.execute(select(Workspace).where(Workspace.slug == body.slug))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug '{body.slug}' is already taken",
        )
    ws_id = str(ulid.new())
    workspace = Workspace(
        id=ws_id,
        name=body.name,
        slug=body.slug,
        owner_id=current_user.id,
    )
    db.add(workspace)
    # Add owner as member
    member = WorkspaceMember(
        id=str(ulid.new()),
        workspace_id=ws_id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    await get_workspace_member(workspace_id, current_user, db)
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
        )
    )
    workspace = result.scalars().first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
        )
    )
    workspace = result.scalars().first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if body.name is not None:
        workspace.name = body.name
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner"])
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
        )
    )
    workspace = result.scalars().first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    from datetime import datetime, timezone
    workspace.deleted_at = datetime.now(timezone.utc)
    await db.commit()


# ── Members ───────────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceMember]:
    await get_workspace_member(workspace_id, current_user, db)
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    )
    return list(result.scalars().all())


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    workspace_id: str,
    body: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember:
    """Invite a user to the workspace by email."""
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])

    result = await db.execute(select(User).where(User.email == str(body.email)))
    invitee = result.scalars().first()
    if invitee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that email address",
        )

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == invitee.id,
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this workspace",
        )

    from datetime import datetime, timezone
    member = WorkspaceMember(
        id=str(ulid.new()),
        workspace_id=workspace_id,
        user_id=invitee.id,
        role=body.role,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove workspace owner"
        )
    await db.delete(member)
    await db.commit()
