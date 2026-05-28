"""Workspace CRUD and member management endpoints."""

from __future__ import annotations

import ulid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

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
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> list[Workspace]:
    """List all workspaces the authenticated user is a member of."""
    memberships = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == current_user.id)
        .all()
    )
    workspace_ids = [m.workspace_id for m in memberships]
    return (
        db.query(Workspace)
        .filter(Workspace.id.in_(workspace_ids), Workspace.deleted_at.is_(None))
        .all()
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    body: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> Workspace:
    """Create a new workspace owned by the current user."""
    existing = db.query(Workspace).filter(Workspace.slug == body.slug).first()
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
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> Workspace:
    get_workspace_member(workspace_id, current_user, db)
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
    ).first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> Workspace:
    get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
    ).first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if body.name is not None:
        workspace.name = body.name
    db.commit()
    db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> None:
    get_workspace_member(workspace_id, current_user, db, required_roles=["owner"])
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
    ).first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    from datetime import datetime, timezone
    workspace.deleted_at = datetime.now(timezone.utc)
    db.commit()


# ── Members ───────────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
def list_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> list[WorkspaceMember]:
    get_workspace_member(workspace_id, current_user, db)
    return (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .all()
    )


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    workspace_id: str,
    body: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> WorkspaceMember:
    """Invite a user to the workspace by email."""
    get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])

    invitee = db.query(User).filter(User.email == str(body.email)).first()
    if invitee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that email address",
        )

    existing = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == invitee.id,
        )
        .first()
    )
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
    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> None:
    get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin"])
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove workspace owner"
        )
    db.delete(member)
    db.commit()
