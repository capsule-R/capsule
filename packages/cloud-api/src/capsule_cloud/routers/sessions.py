"""Session upload, listing, retrieval, and deletion endpoints."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from datetime import datetime, timedelta, timezone

import ulid
import zstandard as zstd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from capsule_cloud.auth import authenticate_api_key, get_current_user, get_workspace_member
from capsule_cloud.config import get_settings
from capsule_cloud.database import get_db
from capsule_cloud.models import ApiKey, Session as CloudSession, User, Workspace
from capsule_cloud.schemas import (
    SessionListResponse,
    SessionResponse,
    SessionUploadMetadata,
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


async def _resolve_user_and_workspace(
    workspace_id: str,
    credentials_header: str | None,
    db: AsyncSession,
    current_user: User | None,
) -> tuple[User, Workspace]:
    """Accept either JWT user or API-key user."""
    ws = await _get_workspace_or_404(workspace_id, db)
    return current_user, ws  # type: ignore[return-value]


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
        raw_tar = dctx.decompress(raw)
        with tarfile.open(fileobj=io.BytesIO(raw_tar)) as tar:
            for member in tar.getmembers():
                if member.name.endswith("session.json"):
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
    error_type = session_json.get("error_type")
    error_message = session_json.get("error_message")

    # Storage path — in production this would be the R2/S3 object key
    storage_path = f"{workspace_id}/{meta.session_id}.capsule"
    
    # Save the file to local disk for development
    import os
    local_storage_dir = os.path.join(os.getcwd(), "data", "storage", workspace_id)
    os.makedirs(local_storage_dir, exist_ok=True)
    with open(os.path.join(local_storage_dir, f"{meta.session_id}.capsule"), "wb") as f:
        f.write(raw)

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
    limit: int = 20,
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
    # Ensure session exists and is not deleted
    await _get_session_or_404(workspace_id, session_id, db)
    
    import os
    local_storage_dir = os.path.join(os.getcwd(), "data", "storage", workspace_id)
    capsule_path = os.path.join(local_storage_dir, f"{session_id}.capsule")
    
    if not os.path.exists(capsule_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session binary data not found on disk."
        )
        
    try:
        with open(capsule_path, "rb") as f:
            raw = f.read()
            
        dctx = zstd.ZstdDecompressor()
        raw_tar = dctx.decompress(raw)
        
        events = []
        with tarfile.open(fileobj=io.BytesIO(raw_tar)) as tar:
            for member in tar.getmembers():
                if member.name.startswith("events/") and member.name.endswith(".json"):
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
        storage_size_bytes=session.storage_size_bytes,
        tags=tags,
        error_type=session.error_type,
        error_message=session.error_message,
        uploaded_at=session.uploaded_at,
        expires_at=session.expires_at,
    )
