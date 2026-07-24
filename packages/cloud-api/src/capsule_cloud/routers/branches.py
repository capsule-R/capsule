from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import get_current_user, get_workspace_member
from capsule_cloud.database import get_db
from capsule_cloud.models import User

router = APIRouter(prefix="/workspaces/{workspace_id}/branches", tags=["branches"])

# In-process branch registry, keyed by workspace_id. Populated by the
# session branch endpoint in sessions.py until DB persistence lands.
BRANCH_STORE: dict[str, list[dict]] = {}


@router.get("", response_model=list[dict])
async def list_branches(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List branches for a workspace.

    Branches created via the session fork endpoint are tracked in an
    in-process store until replay-engine persistence lands.
    """
    await get_workspace_member(workspace_id, current_user, db)
    return BRANCH_STORE.get(workspace_id, [])
