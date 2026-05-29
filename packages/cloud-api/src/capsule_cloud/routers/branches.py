from fastapi import APIRouter, Depends
from typing import List, Dict

from capsule_cloud.auth import get_current_user
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
    """Temporary mock endpoint for branches until replay engine is fully integrated."""
    # Return mock branches from the dashboard
    return [
        {
            "id": "br_9a2f1c",
            "name": "fix-schema-01",
            "originSession": "sess_8f2a91c4",
            "originStep": 4,
            "project": ["checkout-agent", "var(--accent)"],
            "status": "open",
            "replays": 2,
            "author": "dana@helix.ai",
            "age": "3d ago",
            "note": "Remove refund_window column from query"
        },
        {
            "id": "br_2b8d44",
            "name": "retry-timeout-02",
            "originSession": "sess_1a2b3c4d",
            "originStep": 5,
            "project": ["support-triage", "var(--replay)"],
            "status": "merged",
            "replays": 1,
            "author": "marcus@helix.ai",
            "age": "1d ago",
            "note": "Fix LLM timeout by bumping to 60s"
        }
    ]
