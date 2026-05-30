from fastapi import APIRouter, Depends
from typing import List, Dict

from capsule_cloud.auth import get_current_user, get_workspace_member
from capsule_cloud.database import get_db
from capsule_cloud.models import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/workspaces/{workspace_id}/branches", tags=["branches"])

@router.get("", response_model=List[Dict])
async def list_branches(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List branches for a workspace.

    Branches are produced by forking a session in the replay engine, which is
    not yet wired into the cloud. Until persistence lands, this returns an empty
    list rather than mock data — the UI renders its real "no branches" state.
    """
    await get_workspace_member(workspace_id, current_user, db)
    return []
