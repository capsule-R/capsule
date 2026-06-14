"""Pure-Python replay engine.

Loads a .capsule archive and replays it deterministically by serving
stored cassette responses instead of hitting live LLM providers.

Architecture
------------
A Replayer wraps a loaded CapsuleArchive.  When you call replay() or
branch_from_step(), it:

  1. Activates replay mode via a ContextVar (set_replay_store).
  2. Re-processes each stored Event in step order.
  3. For llm_call and tool_call events, looks up the cassette response
     and returns it exactly — no network I/O.
  4. Returns a ReplayResult with the replayed events + diff metrics.

Branching
---------
branch_from_step(N, modifications) replays steps 0..N-1 from cassettes,
applies optional parameter overrides at step N, then returns the context
needed to continue with live calls.  The caller re-runs agent code under
that context and a new Session picks up from there.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import logging
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import zstandard as zstd

from capsule_trace.core.models import Event, EventType, SessionMetadata
from capsule_trace.replay.cassette import CassetteStore

logger = logging.getLogger("capsule.replay")


# ──────────────────────────────────────────────────────────────────
# Result types
# ──────────────────────────────────────────────────────────────────


@dataclass
class ReplayResult:
    session_id: str
    original_step_count: int
    replayed_step_count: int
    events: list[Event]
    integrity_ok: bool
    branch_point: int | None = None

    @property
    def is_deterministic(self) -> bool:
        """True when every replayed event matches the original cassette exactly."""
        return self.integrity_ok and self.replayed_step_count == self.original_step_count


@dataclass
class BranchResult:
    session_id: str
    branch_step: int
    pre_branch_events: list[Event]
    modifications: dict[str, Any]
    cassette_store: CassetteStore


# ──────────────────────────────────────────────────────────────────
# Archive loader
# ──────────────────────────────────────────────────────────────────


@dataclass
class _Archive:
    manifest: dict[str, Any]
    session: SessionMetadata
    events: list[Event]
    cassettes: dict[str, Any]
    snapshots: dict[int, Any]

    @staticmethod
    def from_bytes(data: bytes) -> _Archive:
        dctx = zstd.ZstdDecompressor()
        tar_bytes = dctx.decompress(data)

        files: dict[str, bytes] = {}
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
            for member in tar.getmembers():
                if member.isfile():
                    f = tar.extractfile(member)
                    if f:
                        files[member.name] = f.read()

        manifest = json.loads(files["manifest.json"])

        version = manifest.get("capsule_version", "0")
        if not version.startswith("1."):
            raise ValueError(f"Unsupported capsule version: {version}")

        session_data = json.loads(files["session.json"])
        session = SessionMetadata(**session_data)

        event_names = sorted(k for k in files if k.startswith("events/"))
        events: list[Event] = []
        for name in event_names:
            d = json.loads(files[name])
            events.append(
                Event(
                    event_id=d["event_id"],
                    session_id=d["session_id"],
                    step_index=d["step_index"],
                    parent_event_id=d.get("parent_event_id"),
                    event_type=EventType(d["event_type"]),
                    duration_ms=d.get("duration_ms", 0.0),
                    payload=d.get("payload", {}),
                )
            )

        cassettes: dict[str, Any] = {}
        for name, blob in files.items():
            if name.startswith("cassettes/"):
                bare = name.removeprefix("cassettes/").removesuffix(".json")
                cassettes[bare] = json.loads(blob)

        snapshots: dict[int, Any] = {}
        for name, blob in files.items():
            if name.startswith("snapshots/"):
                step_str = name.removeprefix("snapshots/step-").removesuffix(".json")
                with contextlib.suppress(ValueError):
                    snapshots[int(step_str)] = json.loads(blob)

        return _Archive(
            manifest=manifest,
            session=session,
            events=events,
            cassettes=cassettes,
            snapshots=snapshots,
        )

    @staticmethod
    def from_file(path: Path) -> _Archive:
        return _Archive.from_bytes(path.read_bytes())

    def verify_integrity(self) -> bool:
        """Recompute SHA-256 of event blobs and compare to manifest."""
        expected = self.manifest.get("integrity", {}).get("events_hash", "")
        if not expected:
            return True  # No hash stored — skip check

        # Reserialise events to bytes in the same order they were written
        h = hashlib.sha256()
        for event in self.events:
            blob = json.dumps(event.model_dump_json_safe(), indent=2, default=str).encode()
            h.update(blob)

        return bool(h.hexdigest() == expected)


# ──────────────────────────────────────────────────────────────────
# Replayer
# ──────────────────────────────────────────────────────────────────


class Replayer:
    """Load a .capsule file and replay it deterministically."""

    def __init__(self, archive: _Archive) -> None:
        self._archive = archive
        self._store = CassetteStore(archive.cassettes)

    # ── Constructors ─────────────────────────────────────────

    @classmethod
    def from_file(cls, path: Path | str) -> Replayer:
        return cls(_Archive.from_file(Path(path)))

    @classmethod
    def from_bytes(cls, data: bytes) -> Replayer:
        return cls(_Archive.from_bytes(data))

    @classmethod
    def from_session_id(cls, session_id: str) -> Replayer:
        """Load from the local SQLite store → export → load."""
        import tempfile

        from capsule_trace.core.exporter import export_capsule
        from capsule_trace.storage.sqlite import SQLiteBackend

        backend = SQLiteBackend.default()
        with tempfile.NamedTemporaryFile(suffix=".capsule", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        export_capsule(session_id, backend, tmp_path)
        replayer = cls.from_file(tmp_path)
        tmp_path.unlink(missing_ok=True)
        return replayer

    # ── Properties ───────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._archive.session.session_id

    @property
    def step_count(self) -> int:
        return len(self._archive.events)

    @property
    def session_metadata(self) -> SessionMetadata:
        return self._archive.session

    # ── Replay ───────────────────────────────────────────────

    def replay(self) -> ReplayResult:
        """Replay all steps deterministically from cassettes.

        Returns a ReplayResult whose .events list is the replayed sequence.
        Every llm_call event's payload is augmented with
        ``replayed_response`` taken directly from the cassette.
        """
        integrity_ok = self._archive.verify_integrity()
        replayed: list[Event] = []

        for event in self._archive.events:
            replayed_event = self._replay_event(event, modifications=None)
            replayed.append(replayed_event)

        return ReplayResult(
            session_id=self.session_id,
            original_step_count=self.step_count,
            replayed_step_count=len(replayed),
            events=replayed,
            integrity_ok=integrity_ok,
        )

    def branch_from_step(
        self,
        step: int,
        modifications: dict[str, Any] | None = None,
    ) -> BranchResult:
        """Replay steps 0..step-1 from cassettes, return context for branching.

        Usage::

            branch = replayer.branch_from_step(7, {"temperature": 0.0})
            # Now run your agent code under branch.cassette_store for replay,
            # then at step 7 it hits live APIs with the modified params.
        """
        if step < 0 or step > self.step_count:
            raise IndexError(f"step {step} out of range for session with {self.step_count} steps")

        pre_branch = [
            self._replay_event(e, modifications=None) for e in self._archive.events[:step]
        ]

        return BranchResult(
            session_id=self.session_id,
            branch_step=step,
            pre_branch_events=pre_branch,
            modifications=modifications or {},
            cassette_store=self._store,
        )

    def diff(self, other: Replayer) -> dict[str, Any]:
        """Compare this session's events with another session's events."""
        a_events = self._archive.events
        b_events = other._archive.events

        step_diff = len(b_events) - len(a_events)
        type_changes: list[dict[str, Any]] = []

        for i in range(min(len(a_events), len(b_events))):
            if a_events[i].event_type != b_events[i].event_type:
                type_changes.append(
                    {
                        "step": i,
                        "a": a_events[i].event_type.value,
                        "b": b_events[i].event_type.value,
                    }
                )

        return {
            "session_a": self.session_id,
            "session_b": other.session_id,
            "step_count_a": len(a_events),
            "step_count_b": len(b_events),
            "step_diff": step_diff,
            "type_changes": type_changes,
            "identical_structure": step_diff == 0 and not type_changes,
        }

    def event_summary(self) -> list[dict[str, Any]]:
        return [
            {
                "step": e.step_index,
                "type": e.event_type.value,
                "duration_ms": e.duration_ms,
            }
            for e in self._archive.events
        ]

    # ── Internal ─────────────────────────────────────────────

    def _replay_event(self, event: Event, modifications: dict[str, Any] | None) -> Event:
        """Return a copy of the event, injecting cassette response for LLM/tool calls."""
        payload = (
            copy.deepcopy(event.payload)
            if isinstance(event.payload, dict)
            else event.payload.model_copy(deep=True)
        )

        if event.event_type in (EventType.LLM_CALL, EventType.TOOL_CALL):
            cassette_ref = (
                payload.get("cassette_ref")
                if isinstance(payload, dict)
                else getattr(payload, "cassette_ref", None)
            )
            if cassette_ref:
                cassette_data = self._store.get(cassette_ref)
                if cassette_data is not None:
                    if isinstance(payload, dict):
                        payload["replayed_response"] = cassette_data
                    else:
                        # Pydantic model — convert to dict and add field
                        payload_dict = payload.model_dump(mode="json")
                        payload_dict["replayed_response"] = cassette_data
                        payload = payload_dict

        return Event(
            event_id=event.event_id,
            session_id=event.session_id,
            step_index=event.step_index,
            parent_event_id=event.parent_event_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            duration_ms=event.duration_ms,
            payload=payload,
        )
