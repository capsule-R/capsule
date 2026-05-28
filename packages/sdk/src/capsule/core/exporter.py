"""Export a captured session to the .capsule binary format."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import zstandard as zstd

from capsule.core.models import (
    CapsuleCompression,
    CapsuleEncryption,
    CapsuleIntegrity,
    CapsuleManifest,
    CapsuleProducer,
)

try:
    from capsule import __version__ as _SDK_VERSION
except ImportError:
    _SDK_VERSION = "0.0.0"


def _sha256_of_files(file_contents: list[bytes]) -> str:
    h = hashlib.sha256()
    for content in file_contents:
        h.update(content)
    return h.hexdigest()


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, default=str).encode("utf-8")


def export_capsule(
    session_id: str,
    storage: Any,
    output_path: Path,
    encryption_key: bytes | None = None,
) -> Path:
    """Build a .capsule archive from a stored session and write it to output_path."""
    session_meta = storage.read_session_metadata(session_id)
    events = storage.read_events(session_id)
    cassettes = storage.read_cassettes(session_id)
    snapshots = storage.read_snapshots(session_id)

    # Build in-memory tar
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        event_blobs: list[bytes] = []
        for idx, event in enumerate(events):
            filename = f"events/{idx + 1:04d}-{event.event_type.value}.json"
            blob = _json_bytes(event.model_dump_json_safe())
            event_blobs.append(blob)
            _add_bytes(tar, filename, blob)

        cassette_blobs: list[bytes] = []
        for cass_id, cass_data in cassettes.items():
            filename = f"cassettes/{cass_id}.json"
            blob = _json_bytes(cass_data)
            cassette_blobs.append(blob)
            _add_bytes(tar, filename, blob)

        snapshot_blobs: list[bytes] = []
        for step_idx, snap_data in snapshots.items():
            filename = f"snapshots/step-{step_idx:04d}.json"
            blob = _json_bytes(snap_data)
            snapshot_blobs.append(blob)
            _add_bytes(tar, filename, blob)

        # session.json
        session_blob = _json_bytes(session_meta.model_dump(mode="json"))
        _add_bytes(tar, "session.json", session_blob)

        # manifest.json — built last so hashes are correct
        manifest = CapsuleManifest(
            created_at=datetime.now(timezone.utc),
            session_id=session_id,
            integrity=CapsuleIntegrity(
                events_hash=_sha256_of_files(event_blobs),
                cassettes_hash=_sha256_of_files(cassette_blobs),
                snapshots_hash=_sha256_of_files(snapshot_blobs),
            ),
            encryption=CapsuleEncryption(enabled=encryption_key is not None),
            producer=CapsuleProducer(
                sdk_version=_SDK_VERSION,
                platform=platform.machine(),
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            ),
        )
        manifest_blob = _json_bytes(manifest.model_dump(mode="json"))
        _add_bytes(tar, "manifest.json", manifest_blob)

    raw_tar = tar_buffer.getvalue()

    # Compress with zstd
    cctx = zstd.ZstdCompressor(level=3)
    compressed = cctx.compress(raw_tar)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(compressed)
    return output_path


def _add_bytes(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))
