"""Unit tests for Session and @trace decorator."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from capsule_trace.core.decorator import trace
from capsule_trace.core.models import EventType, SessionStatus
from capsule_trace.core.session import Session
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture()
def in_memory_backend(tmp_path):
    return SQLiteBackend(tmp_path / "test.db")


# ── Session context manager ───────────────────────────────────


def test_session_success(in_memory_backend):
    with Session(agent_name="test-agent", storage_backend=in_memory_backend) as s:
        session_id = s.session_id

    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.SUCCESS
    assert meta.agent_name == "test-agent"
    assert meta.ended_at is not None


def test_session_captures_exception(in_memory_backend):
    session_id = None
    with (
        pytest.raises(ValueError),
        Session(agent_name="failing-agent", storage_backend=in_memory_backend) as s,
    ):
        session_id = s.session_id
        raise ValueError("something went wrong")

    assert session_id is not None
    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.FAILED
    assert meta.error is not None
    assert meta.error.type == "ValueError"
    assert "something went wrong" in meta.error.message


def test_session_tags_and_metadata(in_memory_backend):
    with Session(
        agent_name="tag-test",
        tags=["prod", "billing"],
        user_metadata={"customer_id": "cust_001"},
        storage_backend=in_memory_backend,
    ) as s:
        session_id = s.session_id

    meta = in_memory_backend.read_session_metadata(session_id)
    assert "prod" in meta.tags
    assert "billing" in meta.tags
    assert meta.user_metadata["customer_id"] == "cust_001"


# ── Async session context manager ────────────────────────────


@pytest.mark.asyncio
async def test_async_session_success(in_memory_backend):
    async with Session(agent_name="async-agent", storage_backend=in_memory_backend) as s:
        session_id = s.session_id

    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.SUCCESS


@pytest.mark.asyncio
async def test_async_session_captures_exception(in_memory_backend):
    session_id = None
    with pytest.raises(RuntimeError):
        async with Session(agent_name="async-fail", storage_backend=in_memory_backend) as s:
            session_id = s.session_id
            raise RuntimeError("async boom")

    assert session_id is not None
    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.FAILED


# ── @trace decorator ──────────────────────────────────────────


def test_trace_decorator_sync(in_memory_backend):
    @trace(agent_name="decorated-agent", storage_backend=in_memory_backend)
    def my_fn():
        return 42

    result = my_fn()
    assert result == 42

    sessions = in_memory_backend.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].agent_name == "decorated-agent"
    assert sessions[0].status == SessionStatus.SUCCESS


@pytest.mark.asyncio
async def test_trace_decorator_async(in_memory_backend):
    @trace(agent_name="async-decorated", storage_backend=in_memory_backend)
    async def my_async_fn():
        return "hello"

    result = await my_async_fn()
    assert result == "hello"

    sessions = in_memory_backend.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].status == SessionStatus.SUCCESS


def test_trace_disabled_by_env(in_memory_backend):
    @trace(agent_name="disabled-agent", storage_backend=in_memory_backend)
    def my_fn():
        return 99

    with patch.dict(os.environ, {"CAPSULE_DISABLE": "1"}):
        result = my_fn()

    assert result == 99
    sessions = in_memory_backend.list_sessions()
    assert len(sessions) == 0


def test_trace_preserves_return_value_on_exception(in_memory_backend):
    @trace(agent_name="exception-agent", storage_backend=in_memory_backend)
    def raising_fn():
        raise TypeError("bad type")

    with pytest.raises(TypeError):
        raising_fn()

    sessions = in_memory_backend.list_sessions()
    assert sessions[0].status == SessionStatus.FAILED


# ── Event capture ─────────────────────────────────────────────


def test_capture_event_increments_step_count(in_memory_backend):
    from capsule_trace.core.models import Event

    with Session(agent_name="event-test", storage_backend=in_memory_backend) as s:
        session_id = s.session_id
        for _ in range(3):
            event = Event(
                session_id=s.session_id,
                step_index=s.next_step_index(),
                event_type=EventType.USER_MESSAGE,
                payload={"text": "hello"},
            )
            s.capture_event(event)

    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.step_count == 3


def test_capture_event_never_raises(in_memory_backend):
    """Capture must swallow all internal errors without propagating to user code."""
    with Session(agent_name="safe-test", storage_backend=in_memory_backend) as s:
        bad_event = MagicMock(side_effect=RuntimeError("internal crash"))
        s.capture_event(bad_event)  # type: ignore[arg-type]
