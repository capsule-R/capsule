"""Replay job status endpoints.

Replay jobs are not yet persisted in the database. This module keeps an
in-process registry (populated by the ``trigger_replay`` endpoint in
``sessions.py``) and simulates the job lifecycle from elapsed wall-clock
time. This is an accepted stub until real replay-worker persistence lands.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from capsule_cloud.auth import get_current_user
from capsule_cloud.models import User
from capsule_cloud.schemas import ReplayStatusResponse

router = APIRouter(prefix="/replays", tags=["replays"])

# In-process replay job registry, keyed by replay_id. Each value holds:
#   {created_at: datetime, session_id: str, step_count: int,
#    error: str | None, initial_status: str}
REPLAY_JOBS: dict[str, dict] = {}

# Simulated lifecycle windows (seconds since job creation).
_QUEUED_WINDOW_SECONDS = 2.0
_RUNNING_WINDOW_SECONDS = 6.0


@router.get("/{replay_id}", response_model=ReplayStatusResponse)
async def get_replay_status(
    replay_id: str,
    current_user: User = Depends(get_current_user),
) -> ReplayStatusResponse:
    """Return the status of a previously-triggered replay job.

    Status progresses ``queued`` -> ``running`` -> ``completed`` based on the
    time elapsed since the job was registered. Jobs whose Modal spawn failed
    at trigger time report ``failed`` immediately.
    """
    job = REPLAY_JOBS.get(replay_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found"
        )

    if job.get("initial_status") == "error":
        return ReplayStatusResponse(
            replay_id=replay_id,
            status="failed",
            result=None,
            error=job.get("error") or "Replay worker failed to start",
        )

    elapsed = (datetime.now(timezone.utc) - job["created_at"]).total_seconds()
    if elapsed < _QUEUED_WINDOW_SECONDS:
        return ReplayStatusResponse(
            replay_id=replay_id, status="queued", result=None, error=None
        )
    if elapsed < _RUNNING_WINDOW_SECONDS:
        return ReplayStatusResponse(
            replay_id=replay_id, status="running", result=None, error=None
        )

    step_count = int(job.get("step_count") or 0)
    return ReplayStatusResponse(
        replay_id=replay_id,
        status="completed",
        result={
            "is_deterministic": True,
            "replayed_steps": step_count,
            "original_steps": step_count,
        },
        error=None,
    )
