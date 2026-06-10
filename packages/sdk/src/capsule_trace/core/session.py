"""Session — represents a single agent execution being captured."""

from __future__ import annotations

import logging
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ulid  # type: ignore[import-untyped]

from capsule_trace.core.context import get_current_session, set_current_session
from capsule_trace.core.models import (
    Event,
    SessionError,
    SessionMetadata,
    SessionStatus,
    TokenUsage,
)

logger = logging.getLogger("capsule")


class Session:
    """Captures a single agent execution and writes it to a storage backend."""

    def __init__(
        self,
        agent_name: str,
        agent_version: str | None = None,
        tags: list[str] | None = None,
        user_metadata: dict[str, Any] | None = None,
        redact: list[str] | None = None,
        auto_upload: bool = False,
        storage_backend: Any | None = None,
    ) -> None:
        from capsule_trace.storage.sqlite import SQLiteBackend

        self.session_id = str(ulid.new())
        self._metadata = SessionMetadata(
            session_id=self.session_id,
            agent_name=agent_name,
            agent_version=agent_version,
            tags=tags or [],
            user_metadata=user_metadata or {},
        )
        self._events: list[Event] = []
        self._step_counter = 0
        self._redact_patterns = redact or []
        self._auto_upload = auto_upload
        self._storage = storage_backend or SQLiteBackend.default()
        self._previous_session: Session | None = None

    # ── Context manager ───────────────────────────────────────

    def __enter__(self) -> "Session":
        self._previous_session = get_current_session()
        set_current_session(self)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.finalize(
                status=SessionStatus.FAILED,
                error=exc_val,
            )
        else:
            self.finalize(status=SessionStatus.SUCCESS)
        set_current_session(self._previous_session)

    # ── Async context manager ─────────────────────────────────

    async def __aenter__(self) -> "Session":
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)

    # ── Event capture ─────────────────────────────────────────

    def capture_event(self, event: Event) -> None:
        """Append an event to this session. Never raises — swallows all errors."""
        try:
            self._events.append(event)
            self._step_counter += 1
            self._metadata.step_count = self._step_counter
            self._storage.write_event(event)
        except Exception:
            logger.debug("capsule: failed to capture event", exc_info=True)

    def next_step_index(self) -> int:
        return self._step_counter

    # ── Finalisation ──────────────────────────────────────────

    def finalize(
        self,
        status: SessionStatus,
        error: BaseException | None = None,
    ) -> None:
        """Mark the session as complete and persist final metadata."""
        try:
            now = datetime.now(timezone.utc)
            self._metadata.ended_at = now
            self._metadata.status = status
            self._metadata.duration_ms = (
                (now - self._metadata.started_at).total_seconds() * 1000
            )

            if error is not None:
                self._metadata.error = SessionError(
                    type=type(error).__name__,
                    message=str(error),
                    stack_trace=traceback.format_exc(),
                )

            self._storage.finalize_session(self._metadata)

            if self._auto_upload:
                self._try_upload()
        except Exception:
            logger.debug("capsule: failed to finalize session", exc_info=True)

    def _try_upload(self) -> None:
        """Best-effort cloud upload — never raises."""
        try:
            from capsule_trace.cloud.uploader import upload_session

            upload_session(self.session_id)
        except Exception:
            logger.debug("capsule: cloud upload failed", exc_info=True)

    # ── Export ────────────────────────────────────────────────

    def export(self, output_path: Path | str) -> Path:
        """Export this session as a .capsule file."""
        from capsule_trace.core.exporter import export_capsule

        return export_capsule(self.session_id, self._storage, Path(output_path))

    # ── Properties ────────────────────────────────────────────

    @property
    def session_id(self) -> str:  # type: ignore[override]
        return self._session_id

    @session_id.setter
    def session_id(self, value: str) -> None:
        self._session_id = value

    @property
    def metadata(self) -> SessionMetadata:
        return self._metadata

    @property
    def events(self) -> list[Event]:
        return list(self._events)

    def __repr__(self) -> str:
        return (
            f"Session(id={self.session_id!r}, "
            f"agent={self._metadata.agent_name!r}, "
            f"steps={self._step_counter})"
        )
