"""Replay job status endpoints.

Replay jobs are persisted in the ``replays`` table (see models.Replay) so
their status/result survive process restarts and are visible across every
API replica. Local (in-process) replays write their real result at trigger
time; Modal-queued replays are updated in place once the worker finishes
(see replay_worker.py's _write_result). This endpoint never fabricates a
verdict — a job whose worker hasn't reported back yet stays "queued".
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import get_current_user, get_workspace_member
from capsule_cloud.database import get_db
from capsule_cloud.models import Replay, User
from capsule_cloud.schemas import ReplayStatusResponse

router = APIRouter(prefix="/replays", tags=["replays"])


@router.get("/{replay_id}", response_model=ReplayStatusResponse)
async def get_replay_status(
    replay_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReplayStatusResponse:
    """Return the real, persisted status of a previously-triggered replay job."""
    result = await db.execute(select(Replay).where(Replay.id == replay_id))
    replay = result.scalars().first()
    if replay is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found"
        )

    # IDOR fix: previously any authenticated user could poll any replay_id
    # and see another tenant's session id, step counts, and replay stdout.
    await get_workspace_member(replay.workspace_id, current_user, db)

    result_dict = json.loads(replay.result_json) if replay.result_json else None

    return ReplayStatusResponse(
        replay_id=replay.id,
        status=replay.status,
        result=result_dict,
        error=replay.error_message,
    )
