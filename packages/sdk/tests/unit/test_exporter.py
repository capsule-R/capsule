"""Unit tests for .capsule file export and import roundtrip."""

from __future__ import annotations

import io
import json
import tarfile

import pytest
import zstandard as zstd

from capsule_trace.core.models import Event, EventType, SessionMetadata, SessionStatus
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture()
def backend_with_session(tmp_path):
    backend = SQLiteBackend(tmp_path / "test.db")
    meta = SessionMetadata(
        session_id="ses_test001",
        agent_name="test-agent",
        status=SessionStatus.FAILED,
        step_count=2,
    )
    backend.finalize_session(meta)

    for i in range(2):
        event = Event(
            session_id="ses_test001",
            step_index=i,
            event_type=EventType.LLM_CALL,
            duration_ms=100.0 * (i + 1),
            payload={
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": f"step {i}"}],
            },
        )
        backend.write_event(event)

    backend.write_cassette("llm-0001", {"session_id": "ses_test001", "data": "mock"})
    return backend


def test_export_creates_file(tmp_path, backend_with_session):
    from capsule_trace.core.exporter import export_capsule

    output = tmp_path / "output.capsule"
    result = export_capsule("ses_test001", backend_with_session, output)

    assert result.exists()
    assert result.stat().st_size > 0


def test_export_is_valid_zstd(tmp_path, backend_with_session):
    from capsule_trace.core.exporter import export_capsule

    output = tmp_path / "output.capsule"
    export_capsule("ses_test001", backend_with_session, output)

    raw = output.read_bytes()
    # zstd magic bytes (little-endian: 0xFD2FB528)
    assert raw[:4] == bytes([0x28, 0xB5, 0x2F, 0xFD])


def test_export_contains_required_files(tmp_path, backend_with_session):
    from capsule_trace.core.exporter import export_capsule

    output = tmp_path / "output.capsule"
    export_capsule("ses_test001", backend_with_session, output)

    raw = output.read_bytes()
    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(raw)

    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        names = tar.getnames()

    assert "manifest.json" in names
    assert "session.json" in names
    assert any(n.startswith("events/") for n in names)


def test_export_manifest_has_integrity_hashes(tmp_path, backend_with_session):
    from capsule_trace.core.exporter import export_capsule

    output = tmp_path / "output.capsule"
    export_capsule("ses_test001", backend_with_session, output)

    raw = output.read_bytes()
    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(raw)

    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        f = tar.extractfile("manifest.json")
        assert f is not None
        manifest = json.loads(f.read())

    assert manifest["integrity"]["events_hash"] != ""
    assert manifest["capsule_version"] == "1.0"


def test_import_roundtrip(tmp_path, backend_with_session):
    from capsule_trace.core.exporter import export_capsule

    output = tmp_path / "roundtrip.capsule"
    export_capsule("ses_test001", backend_with_session, output)

    # Simpler: just verify the file can be decompressed and contains expected structure
    raw = output.read_bytes()
    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(raw)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        f = tar.extractfile("session.json")
        assert f is not None
        session_data = json.loads(f.read())

    assert session_data["session_id"] == "ses_test001"
    assert session_data["agent_name"] == "test-agent"


def test_import_capsule_file(tmp_path, backend_with_session, monkeypatch):
    """Full export→import round-trip through import_capsule_file."""
    from capsule_trace.core.exporter import export_capsule
    from capsule_trace.core.importer import import_capsule_file

    output = tmp_path / "roundtrip.capsule"
    export_capsule("ses_test001", backend_with_session, output)

    import_backend = SQLiteBackend(tmp_path / "import.db")
    monkeypatch.setattr(
        "capsule_trace.storage.sqlite.SQLiteBackend.default",
        classmethod(lambda cls: import_backend),
    )

    session_id = import_capsule_file(output)
    assert session_id == "ses_test001"

    meta = import_backend.read_session_metadata(session_id)
    assert meta.agent_name == "test-agent"
    assert meta.status.value == "failed"

    events = import_backend.read_events(session_id)
    assert len(events) == 2
