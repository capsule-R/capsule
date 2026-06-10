"""SQLite storage backend — default local store at ~/.capsule/sessions.db."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session as OrmSession, sessionmaker

from capsule_trace.core.models import Event, EventType, SessionMetadata, SessionStatus

logger = logging.getLogger("capsule.storage")


class _Base(DeclarativeBase):
    pass


class _SessionRow(_Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    agent_name = Column(String, nullable=False)
    agent_version = Column(String)
    started_at = Column(String, nullable=False)
    ended_at = Column(String)
    duration_ms = Column(Float)
    status = Column(String, nullable=False, default="in_progress")
    error_json = Column(Text)
    tags_json = Column(Text, default="[]")
    user_metadata_json = Column(Text, default="{}")
    step_count = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)


class _EventRow(_Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False)
    session_id = Column(String, nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    parent_event_id = Column(String)
    event_type = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    duration_ms = Column(Float, default=0.0)
    payload_json = Column(Text, nullable=False)


class _CassetteRow(_Base):
    __tablename__ = "cassettes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cassette_id = Column(String, unique=True, nullable=False)
    session_id = Column(String, nullable=False, index=True)
    data_json = Column(Text, nullable=False)


class _SnapshotRow(_Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    data_json = Column(Text, nullable=False)


class SQLiteBackend:
    """Local SQLite storage backend."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        _Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    @classmethod
    def default(cls) -> "SQLiteBackend":
        default_path = Path.home() / ".capsule" / "sessions.db"
        return cls(default_path)

    # ── Write ────────────────────────────────────────────────

    def write_event(self, event: Event) -> None:
        with self._Session() as db:
            row = _EventRow(
                event_id=event.event_id,
                session_id=event.session_id,
                step_index=event.step_index,
                parent_event_id=event.parent_event_id,
                event_type=event.event_type.value,
                timestamp=event.timestamp.isoformat(),
                duration_ms=event.duration_ms,
                payload_json=json.dumps(
                    event.payload
                    if isinstance(event.payload, dict)
                    else event.payload.model_dump(mode="json")
                ),
            )
            db.add(row)
            db.commit()

    def write_cassette(self, cassette_id: str, data: dict[str, Any]) -> None:
        with self._Session() as db:
            session_id = data.get("session_id", "")
            existing = (
                db.query(_CassetteRow)
                .filter_by(cassette_id=cassette_id)
                .first()
            )
            if existing is None:
                row = _CassetteRow(
                    cassette_id=cassette_id,
                    session_id=session_id,
                    data_json=json.dumps(data),
                )
                db.add(row)
            else:
                existing.data_json = json.dumps(data)  # type: ignore[assignment]
            db.commit()

    def write_snapshot(self, step_index: int, snapshot: dict[str, Any]) -> None:
        session_id = snapshot.get("session_id", "")
        with self._Session() as db:
            row = _SnapshotRow(
                session_id=session_id,
                step_index=step_index,
                data_json=json.dumps(snapshot),
            )
            db.add(row)
            db.commit()

    def finalize_session(self, metadata: SessionMetadata) -> None:
        with self._Session() as db:
            existing = (
                db.query(_SessionRow)
                .filter_by(session_id=metadata.session_id)
                .first()
            )
            error_json = (
                json.dumps(metadata.error.model_dump()) if metadata.error else None
            )
            if existing is None:
                row = _SessionRow(
                    session_id=metadata.session_id,
                    agent_name=metadata.agent_name,
                    agent_version=metadata.agent_version,
                    started_at=metadata.started_at.isoformat(),
                    ended_at=metadata.ended_at.isoformat() if metadata.ended_at else None,
                    duration_ms=metadata.duration_ms,
                    status=metadata.status.value,
                    error_json=error_json,
                    tags_json=json.dumps(metadata.tags),
                    user_metadata_json=json.dumps(metadata.user_metadata),
                    step_count=metadata.step_count,
                    total_input_tokens=metadata.total_tokens.input,
                    total_output_tokens=metadata.total_tokens.output,
                    total_cost_usd=metadata.total_cost_usd,
                )
                db.add(row)
            else:
                existing.ended_at = metadata.ended_at.isoformat() if metadata.ended_at else None  # type: ignore[assignment]
                existing.duration_ms = metadata.duration_ms  # type: ignore[assignment]
                existing.status = metadata.status.value  # type: ignore[assignment]
                existing.error_json = error_json  # type: ignore[assignment]
                existing.step_count = metadata.step_count  # type: ignore[assignment]
            db.commit()

    # ── Read ─────────────────────────────────────────────────

    def read_session_metadata(self, session_id: str) -> SessionMetadata:
        with self._Session() as db:
            row = db.query(_SessionRow).filter_by(session_id=session_id).first()
            if row is None:
                raise KeyError(f"Session not found: {session_id}")
            return self._row_to_metadata(row)

    def read_events(self, session_id: str) -> list[Event]:
        with self._Session() as db:
            rows = (
                db.query(_EventRow)
                .filter_by(session_id=session_id)
                .order_by(_EventRow.step_index)
                .all()
            )
            return [self._row_to_event(r) for r in rows]

    def read_cassettes(self, session_id: str) -> dict[str, Any]:
        with self._Session() as db:
            rows = (
                db.query(_CassetteRow).filter_by(session_id=session_id).all()
            )
            return {r.cassette_id: json.loads(r.data_json) for r in rows}  # type: ignore[union-attr]

    def read_snapshots(self, session_id: str) -> dict[int, Any]:
        with self._Session() as db:
            rows = (
                db.query(_SnapshotRow)
                .filter_by(session_id=session_id)
                .order_by(_SnapshotRow.step_index)
                .all()
            )
            return {r.step_index: json.loads(r.data_json) for r in rows}  # type: ignore[union-attr]

    def list_sessions(self, limit: int = 50) -> list[SessionMetadata]:
        with self._Session() as db:
            rows = (
                db.query(_SessionRow)
                .order_by(_SessionRow.started_at.desc())
                .limit(limit)
                .all()
            )
            return [self._row_to_metadata(r) for r in rows]

    def delete_session(self, session_id: str) -> None:
        with self._Session() as db:
            db.query(_EventRow).filter_by(session_id=session_id).delete()
            db.query(_CassetteRow).filter_by(session_id=session_id).delete()
            db.query(_SnapshotRow).filter_by(session_id=session_id).delete()
            db.query(_SessionRow).filter_by(session_id=session_id).delete()
            db.commit()

    # ── Conversions ───────────────────────────────────────────

    def _row_to_metadata(self, row: _SessionRow) -> SessionMetadata:
        from datetime import datetime

        error = None
        if row.error_json:  # type: ignore[truthy-bool]
            from capsule_trace.core.models import SessionError

            error = SessionError(**json.loads(row.error_json))  # type: ignore[arg-type]

        return SessionMetadata(
            session_id=str(row.session_id),
            agent_name=str(row.agent_name),
            agent_version=str(row.agent_version) if row.agent_version else None,
            started_at=datetime.fromisoformat(str(row.started_at)),
            ended_at=datetime.fromisoformat(str(row.ended_at)) if row.ended_at else None,
            duration_ms=float(row.duration_ms) if row.duration_ms is not None else None,
            status=SessionStatus(str(row.status)),
            error=error,
            tags=json.loads(str(row.tags_json) or "[]"),
            user_metadata=json.loads(str(row.user_metadata_json) or "{}"),
            step_count=int(row.step_count or 0),  # type: ignore[arg-type]
            total_cost_usd=float(row.total_cost_usd or 0),  # type: ignore[arg-type]
        )

    def _row_to_event(self, row: _EventRow) -> Event:
        from datetime import datetime

        payload = json.loads(str(row.payload_json))
        return Event(
            event_id=str(row.event_id),
            session_id=str(row.session_id),
            step_index=int(row.step_index),  # type: ignore[arg-type]
            parent_event_id=str(row.parent_event_id) if row.parent_event_id else None,
            event_type=EventType(str(row.event_type)),
            timestamp=datetime.fromisoformat(str(row.timestamp)),
            duration_ms=float(row.duration_ms or 0),  # type: ignore[arg-type]
            payload=payload,
        )
