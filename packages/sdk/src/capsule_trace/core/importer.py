"""Import a .capsule file back into the local SQLite store."""

from __future__ import annotations

import io
import json
import tarfile
from typing import TYPE_CHECKING

import zstandard as zstd

if TYPE_CHECKING:
    from pathlib import Path

from capsule_trace.core.models import (
    CapsuleManifest,
    Event,
    EventType,
    SessionMetadata,
)


def import_capsule_file(path: Path) -> str:
    """Decompress, verify, and load a .capsule file into the default SQLite store."""
    from capsule_trace.storage.sqlite import SQLiteBackend

    backend = SQLiteBackend.default()

    raw = path.read_bytes()
    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(raw)

    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
        for member in tar.getmembers():
            if member.isfile():
                f = tar.extractfile(member)
                if f:
                    files[member.name] = f.read()

    # Parse manifest
    manifest_data = json.loads(files["manifest.json"])
    manifest = CapsuleManifest(**manifest_data)
    session_id = manifest.session_id

    # Parse session
    session_data = json.loads(files["session.json"])
    meta = SessionMetadata(**session_data)

    # Persist session
    backend.finalize_session(meta)

    # Persist events
    event_files = sorted(k for k in files if k.startswith("events/"))
    for ef in event_files:
        event_data = json.loads(files[ef])
        event = Event(
            event_id=event_data["event_id"],
            session_id=event_data["session_id"],
            step_index=event_data["step_index"],
            event_type=EventType(event_data["event_type"]),
            duration_ms=event_data.get("duration_ms", 0.0),
            payload=event_data.get("payload", {}),
        )
        backend.write_event(event)

    # Persist cassettes
    for name, blob in files.items():
        if name.startswith("cassettes/"):
            cass_data = json.loads(blob)
            cass_id = name.removeprefix("cassettes/").removesuffix(".json")
            cass_data["session_id"] = session_id
            backend.write_cassette(cass_id, cass_data)

    # Persist snapshots
    for name, blob in files.items():
        if name.startswith("snapshots/"):
            snap_data = json.loads(blob)
            snap_data["session_id"] = session_id
            step_str = name.removeprefix("snapshots/step-").removesuffix(".json")
            backend.write_snapshot(int(step_str), snap_data)

    return session_id
