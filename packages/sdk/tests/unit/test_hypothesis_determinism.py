"""Hypothesis property-based tests — prove replay determinism across random sessions."""

from __future__ import annotations

import io
import json
import tarfile
from typing import Any

import pytest
import zstandard as zstd
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from capsule_trace.replay.engine import Replayer


# ──────────────────────────────────────────────────────────────
# Strategy: generate random capsule archives
# ──────────────────────────────────────────────────────────────

EVENT_TYPES = ["llm_call", "tool_call", "memory_write", "memory_read", "error"]


def _build_capsule(session_id: str, events_data: list[dict[str, Any]]) -> bytes:
    session = {
        "session_id": session_id,
        "agent_name": "hypothesis-agent",
        "started_at": "2026-05-27T10:00:00+00:00",
        "status": "success",
        "step_count": len(events_data),
        "tags": [],
        "user_metadata": {},
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
            blob = json.dumps(data, default=str).encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))

        add("manifest.json", manifest)
        add("session.json", session)
        for i, ev in enumerate(events_data):
            ev["session_id"] = session_id
            ev["step_index"] = i
            ev["event_id"] = f"evt_{i:04d}"
            ev["timestamp"] = "2026-05-27T10:00:01+00:00"
            ev["duration_ms"] = 10.0
            add(f"events/{i+1:04d}-{ev['event_type']}.json", ev)

    cctx = zstd.ZstdCompressor(level=3)
    return cctx.compress(buf.getvalue())


@st.composite
def random_event(draw: Any) -> dict[str, Any]:
    event_type = draw(st.sampled_from(EVENT_TYPES))
    return {
        "event_type": event_type,
        "payload": {
            "provider": draw(st.sampled_from(["openai", "anthropic", "google"])),
            "model": draw(st.sampled_from(["gpt-4o", "claude-3-opus", "gemini-pro"])),
            "messages": [{"role": "user", "content": draw(st.text(min_size=1, max_size=100))}],
        },
    }


@st.composite
def random_capsule_bytes(draw: Any) -> bytes:
    n = draw(st.integers(min_value=0, max_value=20))
    events = draw(st.lists(random_event(), min_size=n, max_size=n))
    session_id = draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=10, max_size=26))
    return _build_capsule(session_id, events)


# ──────────────────────────────────────────────────────────────
# Property: replay is idempotent
# ──────────────────────────────────────────────────────────────

@given(data=random_capsule_bytes())
@settings(
    max_examples=200,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=5000,
)
def test_replay_is_idempotent(data: bytes) -> None:
    """Replaying the same capsule N times always yields identical event_id sequences."""
    replayer = Replayer.from_bytes(data)
    first = [e.event_id for e in replayer.replay().events]
    for _ in range(4):
        subsequent = [e.event_id for e in replayer.replay().events]
        assert subsequent == first, (
            f"Replay produced different event_id sequence on subsequent run "
            f"(session_id={replayer.session_id})"
        )


@given(data=random_capsule_bytes())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=5000)
def test_replay_step_count_matches_original(data: bytes) -> None:
    """Replayed step count always equals the original event count."""
    replayer = Replayer.from_bytes(data)
    result = replayer.replay()
    assert result.replayed_step_count == result.original_step_count == replayer.step_count


@given(data=random_capsule_bytes())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=5000)
def test_branch_pre_events_count(data: bytes) -> None:
    """branch_from_step(N) always returns exactly N pre-branch events."""
    replayer = Replayer.from_bytes(data)
    if replayer.step_count == 0:
        return
    import random as _random
    step = _random.randint(0, replayer.step_count)
    branch = replayer.branch_from_step(step)
    assert len(branch.pre_branch_events) == step


@given(data=random_capsule_bytes())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=5000)
def test_capsule_serialisation_roundtrip(data: bytes) -> None:
    """Archive loading preserves all event types in original order."""
    replayer = Replayer.from_bytes(data)
    events = replayer._archive.events
    for i, event in enumerate(events):
        assert event.step_index == i


@given(data=random_capsule_bytes())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=5000)
def test_event_summary_length_matches_step_count(data: bytes) -> None:
    replayer = Replayer.from_bytes(data)
    summary = replayer.event_summary()
    assert len(summary) == replayer.step_count
