"""Unit tests for the Capsule replay engine."""

from __future__ import annotations

import io
import json
import tarfile

import pytest
import zstandard as zstd

from capsule_trace.core.models import EventType
from capsule_trace.replay.cassette import CassetteStore
from capsule_trace.replay.engine import Replayer
from capsule_trace.storage.sqlite import SQLiteBackend

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _make_capsule_bytes(
    session_id: str = "ses_test",
    n_events: int = 3,
    include_cassettes: bool = True,
) -> bytes:
    """Build a minimal in-memory .capsule archive."""
    session = {
        "session_id": session_id,
        "agent_name": "test-agent",
        "started_at": "2026-05-27T10:00:00+00:00",
        "ended_at": "2026-05-27T10:00:05+00:00",
        "status": "success",
        "step_count": n_events,
        "tags": [],
        "user_metadata": {},
    }

    events = []
    cassettes = {}
    for i in range(n_events):
        cass_id = f"llm-{i:04d}"
        cass_ref = f"cassettes/{cass_id}.json"
        events.append(
            {
                "event_id": f"evt_{i:03d}",
                "session_id": session_id,
                "step_index": i,
                "event_type": "llm_call",
                "timestamp": "2026-05-27T10:00:01+00:00",
                "duration_ms": 100.0,
                "payload": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": f"step {i}"}],
                    "cassette_ref": cass_ref,
                },
            }
        )
        if include_cassettes:
            cassettes[cass_id] = {
                "raw_response": {
                    "choices": [{"message": {"content": f"response {i}"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                }
            }

    manifest = {
        "capsule_version": "1.0",
        "format_spec_url": "https://capsule.dev/spec/v1.0",
        "created_at": "2026-05-27T10:00:00Z",
        "session_id": session_id,
        "integrity": {
            "algorithm": "sha256",
            "events_hash": "",
            "cassettes_hash": "",
            "snapshots_hash": "",
        },
        "compression": {"algorithm": "zstd", "level": 3},
        "encryption": {"enabled": False},
        "producer": {
            "sdk_name": "capsule-python",
            "sdk_version": "0.1.0",
            "platform": "test",
            "python_version": "3.13.0",
        },
    }

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:

        def add(name: str, data: dict) -> None:
            blob = json.dumps(data).encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))

        add("manifest.json", manifest)
        add("session.json", session)
        for i, ev in enumerate(events):
            add(f"events/{i + 1:04d}-llm_call.json", ev)
        for cid, cdata in cassettes.items():
            add(f"cassettes/{cid}.json", cdata)

    cctx = zstd.ZstdCompressor(level=3)
    return cctx.compress(buf.getvalue())


# ──────────────────────────────────────────────────────────────
# CassetteStore
# ──────────────────────────────────────────────────────────────


def test_cassette_store_lookup_by_ref():
    store = CassetteStore({"llm-0001": {"data": "foo"}})
    assert store.get("cassettes/llm-0001.json") == {"data": "foo"}
    assert store.get("llm-0001") == {"data": "foo"}
    assert store.get("missing") is None


def test_cassette_store_sequential_pop():
    store = CassetteStore({"a": {"n": 1}, "b": {"n": 2}, "c": {"n": 3}})
    assert store._pop_next() == {"n": 1}
    assert store._pop_next() == {"n": 2}
    assert store._pop_next() == {"n": 3}
    assert store._pop_next() is None


def test_cassette_store_reset():
    store = CassetteStore({"x": {"v": 42}})
    assert store._pop_next() == {"v": 42}
    assert store._pop_next() is None
    store.reset()
    assert store._pop_next() == {"v": 42}


# ──────────────────────────────────────────────────────────────
# Replayer — loading
# ──────────────────────────────────────────────────────────────


def test_replayer_from_bytes():
    data = _make_capsule_bytes("ses_abc", n_events=2)
    r = Replayer.from_bytes(data)
    assert r.session_id == "ses_abc"
    assert r.step_count == 2


def test_replayer_from_file(tmp_path):
    data = _make_capsule_bytes("ses_file", n_events=1)
    p = tmp_path / "test.capsule"
    p.write_bytes(data)
    r = Replayer.from_file(p)
    assert r.session_id == "ses_file"


def test_replayer_unsupported_version():
    data = _make_capsule_bytes()
    # Corrupt capsule_version field
    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(data)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        f = tar.extractfile("manifest.json")
        assert f is not None
        manifest = json.loads(f.read())
    manifest["capsule_version"] = "9.0"

    buf = io.BytesIO()
    with (
        tarfile.open(fileobj=buf, mode="w") as new_tar,
        tarfile.open(fileobj=io.BytesIO(tar_bytes)) as old_tar,
    ):
        # Re-pack with bad version
        for member in old_tar.getmembers():
            if member.name == "manifest.json":
                blob = json.dumps(manifest).encode()
                info = tarfile.TarInfo(name="manifest.json")
                info.size = len(blob)
                new_tar.addfile(info, io.BytesIO(blob))
            else:
                f2 = old_tar.extractfile(member)
                if f2:
                    new_tar.addfile(member, f2)

    cctx = zstd.ZstdCompressor(level=3)
    bad_data = cctx.compress(buf.getvalue())
    with pytest.raises(ValueError, match="Unsupported capsule version"):
        Replayer.from_bytes(bad_data)


# ──────────────────────────────────────────────────────────────
# Replayer — replay()
# ──────────────────────────────────────────────────────────────


def test_replay_returns_all_events():
    data = _make_capsule_bytes(n_events=5)
    result = Replayer.from_bytes(data).replay()
    assert result.replayed_step_count == 5
    assert result.original_step_count == 5
    assert len(result.events) == 5


def test_replay_injects_cassette_into_llm_events():
    data = _make_capsule_bytes(n_events=2)
    result = Replayer.from_bytes(data).replay()
    for event in result.events:
        payload = event.payload if isinstance(event.payload, dict) else event.payload.model_dump()
        assert "replayed_response" in payload


def test_replay_is_deterministic():
    """Replaying the same capsule 10 times produces identical event_ids each time."""
    data = _make_capsule_bytes(n_events=4)
    replayer = Replayer.from_bytes(data)

    first_ids = [e.event_id for e in replayer.replay().events]
    for _ in range(9):
        ids = [e.event_id for e in replayer.replay().events]
        assert ids == first_ids


def test_replay_result_is_deterministic_flag():
    data = _make_capsule_bytes(n_events=3)
    result = Replayer.from_bytes(data).replay()
    assert result.is_deterministic is True


# ──────────────────────────────────────────────────────────────
# Replayer — branch_from_step()
# ──────────────────────────────────────────────────────────────


def test_branch_from_step_zero():
    data = _make_capsule_bytes(n_events=5)
    branch = Replayer.from_bytes(data).branch_from_step(0)
    assert branch.branch_step == 0
    assert len(branch.pre_branch_events) == 0


def test_branch_from_step_middle():
    data = _make_capsule_bytes(n_events=6)
    branch = Replayer.from_bytes(data).branch_from_step(3)
    assert branch.branch_step == 3
    assert len(branch.pre_branch_events) == 3


def test_branch_from_step_last():
    data = _make_capsule_bytes(n_events=4)
    branch = Replayer.from_bytes(data).branch_from_step(4)
    assert len(branch.pre_branch_events) == 4


def test_branch_out_of_range_raises():
    data = _make_capsule_bytes(n_events=3)
    with pytest.raises(IndexError):
        Replayer.from_bytes(data).branch_from_step(99)


def test_branch_carries_modifications():
    data = _make_capsule_bytes(n_events=4)
    mods = {"temperature": 0.0, "seed": 42}
    branch = Replayer.from_bytes(data).branch_from_step(2, mods)
    assert branch.modifications == mods


# ──────────────────────────────────────────────────────────────
# Replayer — diff()
# ──────────────────────────────────────────────────────────────


def test_diff_identical_sessions():
    data = _make_capsule_bytes("ses_a", n_events=3)
    a = Replayer.from_bytes(data)
    b = Replayer.from_bytes(data)  # same data
    diff = a.diff(b)
    # session IDs are both ses_a so structure is identical
    assert diff["identical_structure"] is True
    assert diff["step_diff"] == 0


def test_diff_different_step_counts():
    a = Replayer.from_bytes(_make_capsule_bytes("ses_a", n_events=3))
    b = Replayer.from_bytes(_make_capsule_bytes("ses_b", n_events=5))
    diff = a.diff(b)
    assert diff["step_diff"] == 2
    assert diff["identical_structure"] is False


# ──────────────────────────────────────────────────────────────
# Replayer — from_session_id (round-trip through SQLite)
# ──────────────────────────────────────────────────────────────


def test_replayer_from_session_id(tmp_path):
    """Verify we can export from SQLite and reload via Replayer.from_file."""
    from capsule_trace.core.session import Session

    backend = SQLiteBackend(tmp_path / "test.db")

    with Session(agent_name="roundtrip", storage_backend=backend) as s:
        sid = s.session_id
        from capsule_trace.core.models import Event, LLMCallPayload, LLMMessage

        ev = Event(
            session_id=sid,
            step_index=0,
            event_type=EventType.LLM_CALL,
            duration_ms=50.0,
            payload=LLMCallPayload(
                provider="openai",
                model="gpt-4o",
                messages=[LLMMessage(role="user", content="hi")],
            ),
        )
        s.capture_event(ev)

    from capsule_trace.core.exporter import export_capsule

    out = tmp_path / "test.capsule"
    export_capsule(sid, backend, out)

    replayer = Replayer.from_file(out)
    assert replayer.session_id == sid
    result = replayer.replay()
    assert result.replayed_step_count == 1
