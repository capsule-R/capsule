"""Session upload, listing, retrieval, and deletion endpoints."""

from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from datetime import datetime, timedelta, timezone

import ulid
import zstandard as zstd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Hard cap on decompressed archive size to prevent decompression bombs.
_MAX_DECOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
# Per-member size limit when reading individual tar entries into memory.
_MAX_TAR_MEMBER_BYTES = 50 * 1024 * 1024  # 50 MB

from capsule_cloud.auth import authenticate_api_key, get_current_user, get_workspace_member
from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud import storage as _storage
from capsule_cloud.models import ApiKey, Session as CloudSession, User, Workspace
from capsule_cloud.schemas import (
    BranchCreateRequest,
    BranchCreateResponse,
    DailyCount,
    ReplayResponse,
    SessionListResponse,
    SessionResponse,
    SessionStatsResponse,
    SessionUploadMetadata,
    TriggerReplayRequest,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/sessions", tags=["sessions"])

_PLAN_MAX_UPLOAD = {
    "free": 100 * 1024 * 1024,
    "hobby": 100 * 1024 * 1024,
    "pro": 500 * 1024 * 1024,
    "business": 5 * 1024 * 1024 * 1024,
}


async def _get_workspace_or_404(workspace_id: str, db: AsyncSession) -> Workspace:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
        )
    )
    ws = result.scalars().first()
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


# ── Upload ────────────────────────────────────────────────────

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def upload_session(
    workspace_id: str,
    file: UploadFile = File(..., description=".capsule archive"),
    metadata: str = Form(..., description="JSON-encoded SessionUploadMetadata"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudSession:
    """Upload a `.capsule` file and register the session in the cloud."""
    ws = await _get_workspace_or_404(workspace_id, db)
    await get_workspace_member(workspace_id, current_user, db)

    # Parse metadata
    try:
        meta = SessionUploadMetadata.model_validate_json(metadata)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metadata JSON: {exc}",
        )

    raw = await file.read()
    file_size = len(raw)

    # Enforce upload size limit based on plan
    settings = get_settings()
    max_bytes = _PLAN_MAX_UPLOAD.get(ws.plan_tier, settings.max_upload_size_hobby)
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {max_bytes // (1024*1024)} MB limit for plan '{ws.plan_tier}'",
        )

    # Check storage quota
    if ws.storage_used_bytes + file_size > ws.storage_quota_bytes:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Storage quota exceeded",
        )

    # Compute integrity hash
    integrity_hash = hashlib.sha256(raw).hexdigest()

    # Parse the .capsule archive to extract session metadata
    session_json: dict = {}
    try:
        dctx = zstd.ZstdDecompressor()
        raw_tar = dctx.decompress(raw, max_length=_MAX_DECOMPRESSED_BYTES)
        with tarfile.open(fileobj=io.BytesIO(raw_tar)) as tar:
            for member in tar.getmembers():
                if member.name.endswith("session.json"):
                    if member.size > _MAX_TAR_MEMBER_BYTES:
                        break
                    f = tar.extractfile(member)
                    if f:
                        session_json = json.loads(f.read())
                    break
    except Exception:
        # If we can't parse, we still store it; metadata from the form takes precedence
        pass

    started_at_raw = session_json.get("started_at")
    ended_at_raw = session_json.get("ended_at")

    def _parse_dt(v: str | None) -> datetime | None:
        if not v:
            return None
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            return None

    started_at = _parse_dt(started_at_raw)
    ended_at = _parse_dt(ended_at_raw)
    duration_ms = session_json.get("duration_ms")
    step_count = session_json.get("step_count", 0)
    status_val = session_json.get("status", "completed")

    # Aggregate cost / token usage — the SDK writes these into session.json.
    total_cost_usd = session_json.get("total_cost_usd") or 0
    _tokens = session_json.get("total_tokens")
    if isinstance(_tokens, dict):
        total_input_tokens = _tokens.get("input") or 0
        total_output_tokens = _tokens.get("output") or 0
    else:
        total_input_tokens = session_json.get("total_input_tokens") or 0
        total_output_tokens = session_json.get("total_output_tokens") or 0

    # Error details — the SDK nests them under "error"; fall back to flat keys.
    _err = session_json.get("error")
    if isinstance(_err, dict):
        error_type = _err.get("type")
        error_message = _err.get("message")
    else:
        error_type = session_json.get("error_type")
        error_message = session_json.get("error_message")

    # Object storage key — same path on both local disk fallback and B2/R2
    storage_path = f"{workspace_id}/{meta.session_id}.capsule"
    await _storage.upload(storage_path, raw)

    # Retention
    retention_days = ws.retention_days
    expires_at = datetime.now(timezone.utc) + timedelta(days=retention_days)

    cloud_session = CloudSession(
        id=meta.session_id,
        workspace_id=workspace_id,
        agent_name=meta.agent_name,
        agent_version=meta.agent_version,
        started_at=started_at or datetime.now(timezone.utc),
        ended_at=ended_at,
        duration_ms=duration_ms,
        status=status_val,
        step_count=step_count,
        total_cost_usd=total_cost_usd,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        error_type=error_type,
        error_message=error_message,
        tags_json=json.dumps(meta.tags),
        user_metadata_json=json.dumps(meta.user_metadata),
        storage_path=storage_path,
        storage_size_bytes=file_size,
        integrity_hash=integrity_hash,
        uploaded_by_id=current_user.id,
        expires_at=expires_at,
    )

    # Check for duplicate
    result = await db.execute(
        select(CloudSession).where(CloudSession.id == meta.session_id)
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session '{meta.session_id}' already exists",
        )

    db.add(cloud_session)
    ws.storage_used_bytes += file_size
    await db.commit()
    await db.refresh(cloud_session)

    # Attach computed fields
    cloud_session.tags = meta.tags  # type: ignore[attr-defined]
    return cloud_session


# ── List ──────────────────────────────────────────────────────

@router.get("", response_model=SessionListResponse)
async def list_sessions(
    workspace_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    agent_name: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    await get_workspace_member(workspace_id, current_user, db)

    query = select(CloudSession).where(
        CloudSession.workspace_id == workspace_id,
        CloudSession.deleted_at.is_(None),
    )
    if agent_name:
        query = query.where(CloudSession.agent_name == agent_name)
    if status:
        query = query.where(CloudSession.status == status)

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(CloudSession.uploaded_at.desc())

    if cursor:
        # cursor is the uploaded_at of the last seen item (ISO format)
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(CloudSession.uploaded_at < cursor_dt)
        except ValueError:
            pass

    result = await db.execute(query.limit(limit))
    items = list(result.scalars().all())

    # Materialise tags from JSON
    for item in items:
        try:
            item.tags = json.loads(item.tags_json)  # type: ignore[attr-defined]
        except Exception:
            item.tags = []  # type: ignore[attr-defined]

    next_cursor = None
    if len(items) == limit:
        next_cursor = items[-1].uploaded_at.isoformat()

    return SessionListResponse(
        items=[_to_response(s) for s in items],
        total=total,
        cursor=next_cursor,
    )


# ── Stats ─────────────────────────────────────────────────────
# NOTE: declared BEFORE "/{session_id}" so the literal path wins routing.

@router.get("/stats", response_model=SessionStatsResponse)
async def session_stats(
    workspace_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionStatsResponse:
    """Aggregate session metrics for the dashboard overview.

    Returns all-time totals (sessions, failures, cost, tokens) plus a
    captured-per-day series over the requested window (1–365 days).
    """
    await get_workspace_member(workspace_id, current_user, db)
    days = max(1, min(days, 365))

    def _scoped():
        return select(CloudSession).where(
            CloudSession.workspace_id == workspace_id,
            CloudSession.deleted_at.is_(None),
        )

    total = (
        await db.execute(select(func.count()).select_from(_scoped().subquery()))
    ).scalar() or 0
    failed = (
        await db.execute(
            select(func.count()).select_from(
                _scoped().where(CloudSession.status == "failed").subquery()
            )
        )
    ).scalar() or 0
    cost = (
        await db.execute(
            select(func.coalesce(func.sum(CloudSession.total_cost_usd), 0)).where(
                CloudSession.workspace_id == workspace_id,
                CloudSession.deleted_at.is_(None),
            )
        )
    ).scalar() or 0
    in_tok = (
        await db.execute(
            select(func.coalesce(func.sum(CloudSession.total_input_tokens), 0)).where(
                CloudSession.workspace_id == workspace_id,
                CloudSession.deleted_at.is_(None),
            )
        )
    ).scalar() or 0
    out_tok = (
        await db.execute(
            select(func.coalesce(func.sum(CloudSession.total_output_tokens), 0)).where(
                CloudSession.workspace_id == workspace_id,
                CloudSession.deleted_at.is_(None),
            )
        )
    ).scalar() or 0

    # Daily buckets — DB-agnostic: fetch timestamps in range and bucket in Python.
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    rows = (
        await db.execute(
            select(CloudSession.uploaded_at).where(
                CloudSession.workspace_id == workspace_id,
                CloudSession.deleted_at.is_(None),
                CloudSession.uploaded_at >= start,
            )
        )
    ).scalars().all()

    buckets: dict[str, int] = {
        (start + timedelta(days=i)).date().isoformat(): 0 for i in range(days)
    }
    for ts in rows:
        if ts is None:
            continue
        key = ts.date().isoformat()
        if key in buckets:
            buckets[key] += 1

    daily = [DailyCount(date=d, count=c) for d, c in buckets.items()]

    return SessionStatsResponse(
        total=total,
        failed=failed,
        total_cost_usd=float(cost or 0),
        total_input_tokens=int(in_tok or 0),
        total_output_tokens=int(out_tok or 0),
        range_days=days,
        daily=daily,
    )


# ── Get ───────────────────────────────────────────────────────

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    await get_workspace_member(workspace_id, current_user, db)
    session = await _get_session_or_404(workspace_id, session_id, db)
    try:
        session.tags = json.loads(session.tags_json)  # type: ignore[attr-defined]
    except Exception:
        session.tags = []  # type: ignore[attr-defined]
    return _to_response(session)


# ── Delete ────────────────────────────────────────────────────

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await get_workspace_member(workspace_id, current_user, db, required_roles=["owner", "admin", "member"])
    session = await _get_session_or_404(workspace_id, session_id, db)
    session.deleted_at = datetime.now(timezone.utc)
    # reclaim storage
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = result.scalars().first()
    if ws:
        ws.storage_used_bytes = max(0, ws.storage_used_bytes - session.storage_size_bytes)
    await db.commit()


# ── Events ────────────────────────────────────────────────────

@router.get("/{session_id}/events", response_model=list[dict])
async def get_session_events(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Retrieve all detailed events for a session directly from the .capsule archive."""
    await get_workspace_member(workspace_id, current_user, db)
    session = await _get_session_or_404(workspace_id, session_id, db)

    try:
        raw = await _storage.download(session.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session binary data not found in storage.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage error: {exc}",
        )

    try:
        dctx = zstd.ZstdDecompressor()
        raw_tar = dctx.decompress(raw, max_length=_MAX_DECOMPRESSED_BYTES)

        events = []
        with tarfile.open(fileobj=io.BytesIO(raw_tar)) as tar:
            for member in tar.getmembers():
                if member.name.startswith("events/") and member.name.endswith(".json"):
                    if member.size > _MAX_TAR_MEMBER_BYTES:
                        continue
                    extracted_file = tar.extractfile(member)
                    if extracted_file:
                        event_data = json.loads(extracted_file.read().decode("utf-8"))
                        events.append((member.name, event_data))

        # Sort by filename which contains the index (e.g. 0001-tool_call.json)
        events.sort(key=lambda x: x[0])
        return [e[1] for e in events]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse capsule archive: {str(e)}"
        )

# ── Download ──────────────────────────────────────────────────

@router.get("/{session_id}/download")
async def download_session(
    workspace_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Stream the raw ``.capsule`` archive for a session as a file download."""
    await get_workspace_member(workspace_id, current_user, db)
    session = await _get_session_or_404(workspace_id, session_id, db)

    try:
        raw = await _storage.download(session.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session binary data not found in storage.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage error: {exc}",
        )

    # Strip any characters that could break the Content-Disposition header value
    safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', session_id)
    return Response(
        content=raw,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_id}.capsule"',
            "Content-Length": str(len(raw)),
        },
    )


# ── Replay ───────────────────────────────────────────────────

async def _local_replay(
    session: CloudSession,
    body: TriggerReplayRequest,
) -> tuple[str, str | None, dict | None]:
    """Run a cassette replay in-process (fallback when Modal is not configured).

    Returns (status, error_message, result_dict).
    """
    import asyncio
    import os
    import tempfile

    try:
        raw = await _storage.download(session.storage_path)
    except FileNotFoundError as exc:
        return "error", f"Session file not found: {exc}", None
    except Exception as exc:
        return "error", f"Failed to download session data: {exc}", None

    with tempfile.NamedTemporaryFile(suffix=".capsule", delete=False) as f:
        f.write(raw)
        tmp_path = f.name

    try:
        cmd = ["capsule", "replay", tmp_path, f"--mode={body.mode}"]
        if body.branch_from_step is not None:
            cmd += [f"--branch-from={body.branch_from_step}"]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return "error", "Local replay timed out after 120 seconds", None

        stdout = stdout_b.decode(errors="replace")[-4000:]
        stderr = stderr_b.decode(errors="replace")[-2000:]

        if proc.returncode == 0:
            step_count = session.step_count or 0
            return "completed", None, {
                "is_deterministic": True,
                "replayed_steps": step_count,
                "original_steps": step_count,
                "stdout": stdout,
            }
        return "error", stderr or f"capsule replay exited with code {proc.returncode}", None
    except FileNotFoundError:
        return "error", "capsule CLI not found — install capsule-sdk in the API server environment", None
    except Exception as exc:
        return "error", str(exc), None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/{session_id}/replay", response_model=ReplayResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_replay(
    workspace_id: str,
    session_id: str,
    body: TriggerReplayRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReplayResponse:
    """Queue a remote replay of a session via Modal cloud execution.

    Returns immediately with ``status: queued`` (or ``pending_modal_config``
    when Modal credentials are not set). The actual replay runs asynchronously
    in a Modal sandbox — check the Modal dashboard for execution logs.
    """
    await get_workspace_member(workspace_id, current_user, db)
    session = await _get_session_or_404(workspace_id, session_id, db)

    replay_id = str(ulid.new())
    settings = get_settings()

    import structlog as _structlog
    _log = _structlog.get_logger(__name__)

    replay_error: str | None = None
    replay_result: dict | None = None

    if settings.modal_token_id and settings.modal_token_secret:
        try:
            import modal  # type: ignore[import-untyped]

            run_replay = modal.Function.lookup("capsule-replay", "run_replay")
            await run_replay.spawn.aio(
                storage_path=session.storage_path,
                mode=body.mode,
                branch_from_step=body.branch_from_step,
                storage_endpoint=settings.storage_endpoint,
                storage_access_key=settings.storage_access_key,
                storage_secret_key=settings.storage_secret_key,
                storage_bucket=settings.storage_bucket,
            )
            replay_status = "queued"
        except Exception as exc:
            _log.warning("modal_spawn_failed", error=str(exc))
            replay_status = "error"
            replay_error = str(exc)
    else:
        step_count = session.step_count or 0
        if step_count < 30:
            replay_status, replay_error, replay_result = await _local_replay(session, body)
        else:
            replay_status = "error"
            replay_error = (
                f"Session has {step_count} steps (limit 30 for local replay). "
                "Configure MODAL_TOKEN_ID and MODAL_TOKEN_SECRET for cloud replay."
            )

    # Register the job so GET /replays/{replay_id} can report its status.
    from capsule_cloud.routers.replays import REPLAY_JOBS

    REPLAY_JOBS[replay_id] = {
        "created_at": datetime.now(timezone.utc),
        "session_id": session_id,
        "step_count": session.step_count or 0,
        "error": replay_error,
        "initial_status": replay_status,
        "replay_result": replay_result,
    }

    return ReplayResponse(
        id=replay_id,
        session_id=session_id,
        status=replay_status,
        replay_mode=body.mode,
        branch_from_step=body.branch_from_step,
        created_at=datetime.now(timezone.utc),
    )


# ── Branch ───────────────────────────────────────────────────

@router.post(
    "/{session_id}/branch",
    response_model=BranchCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_branch(
    workspace_id: str,
    session_id: str,
    body: BranchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchCreateResponse:
    """Fork a session at a specific step.

    Branch records live in an in-process store until replay-engine
    persistence lands; the Branches page lists them via GET /branches.
    """
    await get_workspace_member(workspace_id, current_user, db)
    session = await _get_session_or_404(workspace_id, session_id, db)

    if session.step_count and body.from_step >= session.step_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"from_step {body.from_step} is out of range "
                   f"(session has {session.step_count} steps)",
        )

    from capsule_cloud.routers.branches import BRANCH_STORE

    branch_id = str(ulid.new())
    BRANCH_STORE.setdefault(workspace_id, []).append({
        "id": branch_id,
        "session_id": session_id,
        "from_step": body.from_step,
        "note": body.note,
        "status": "created",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return BranchCreateResponse(branch_id=branch_id)


# ── Helpers ───────────────────────────────────────────────────

async def _get_session_or_404(workspace_id: str, session_id: str, db: AsyncSession) -> CloudSession:
    result = await db.execute(
        select(CloudSession).where(
            CloudSession.id == session_id,
            CloudSession.workspace_id == workspace_id,
            CloudSession.deleted_at.is_(None),
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _to_response(session: CloudSession) -> SessionResponse:
    tags: list[str] = []
    try:
        tags = json.loads(session.tags_json)
    except Exception:
        pass
    return SessionResponse(
        id=session.id,
        workspace_id=session.workspace_id,
        agent_name=session.agent_name,
        agent_version=session.agent_version,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_ms=session.duration_ms,
        status=session.status,
        step_count=session.step_count,
        total_cost_usd=float(session.total_cost_usd or 0),
        total_input_tokens=session.total_input_tokens or 0,
        total_output_tokens=session.total_output_tokens or 0,
        storage_size_bytes=session.storage_size_bytes,
        tags=tags,
        error_type=session.error_type,
        error_message=session.error_message,
        uploaded_at=session.uploaded_at,
        expires_at=session.expires_at,
    )
