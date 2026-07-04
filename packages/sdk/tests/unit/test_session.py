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


# ── Redaction (P1) ────────────────────────────────────────────


def _as_dict(payload):
    """Event.payload round-trips through a smart pydantic union — a dict
    shaped like one of the typed payload models (ToolCallPayload etc.) comes
    back out as that model, not a plain dict. Normalize for assertions."""
    return payload if isinstance(payload, dict) else payload.model_dump(mode="json")


def test_redact_masks_matching_dict_payload_field(in_memory_backend):
    """P1: redact=[...] was silently ignored — a matching field must now be
    masked before the event is ever written to storage."""
    from capsule_trace.core.models import Event

    with Session(
        agent_name="redact-test", storage_backend=in_memory_backend, redact=["api_key", "ssn"]
    ) as s:
        session_id = s.session_id
        event = Event(
            session_id=s.session_id,
            step_index=s.next_step_index(),
            event_type=EventType.TOOL_CALL,
            payload={
                "tool_name": "lookup_customer",
                "arguments": {"api_key": "sk-super-secret", "customer_ssn": "123-45-6789"},
                "result": "ok",
            },
        )
        s.capture_event(event)

    events = in_memory_backend.read_events(session_id)
    assert len(events) == 1
    stored = _as_dict(events[0].payload)
    assert stored["arguments"]["api_key"] == "[REDACTED]"
    assert stored["arguments"]["customer_ssn"] == "[REDACTED]"
    assert stored["result"] == "ok"


def test_redact_masks_matching_pydantic_payload_field(in_memory_backend):
    """redact must also apply to pydantic payload models (LLMCallPayload etc),
    not just plain dicts."""
    from capsule_trace.core.models import Event, LLMCallPayload, LLMMessage

    with Session(
        agent_name="redact-pydantic-test", storage_backend=in_memory_backend, redact=["messages"]
    ) as s:
        session_id = s.session_id
        payload = LLMCallPayload(
            provider="openai",
            model="gpt-4o",
            messages=[LLMMessage(role="user", content="my api key is sk-secret-123")],
        )
        event = Event(
            session_id=s.session_id,
            step_index=s.next_step_index(),
            event_type=EventType.LLM_CALL,
            payload=payload,
        )
        s.capture_event(event)

    events = in_memory_backend.read_events(session_id)
    stored = _as_dict(events[0].payload)
    assert stored["messages"] == "[REDACTED]"
    assert stored["model"] == "gpt-4o"  # untouched fields survive


def test_no_redaction_when_patterns_not_configured(in_memory_backend):
    """Sessions created without redact= must behave exactly as before."""
    from capsule_trace.core.models import Event

    with Session(agent_name="no-redact-test", storage_backend=in_memory_backend) as s:
        session_id = s.session_id
        event = Event(
            session_id=s.session_id,
            step_index=s.next_step_index(),
            event_type=EventType.TOOL_CALL,
            payload={"tool_name": "x", "arguments": {"api_key": "sk-not-redacted"}},
        )
        s.capture_event(event)

    events = in_memory_backend.read_events(session_id)
    assert _as_dict(events[0].payload)["arguments"]["api_key"] == "sk-not-redacted"


def test_redact_failure_logs_warning_and_still_stores_event(in_memory_backend, caplog):
    """If redaction itself blows up, the SDK must warn loudly (not silently
    swallow at DEBUG like ordinary capture errors) rather than silently
    storing unredacted data with no trace of the failure."""
    import logging

    with Session(
        agent_name="redact-failure-test", storage_backend=in_memory_backend, redact=["x"]
    ) as s:
        session_id = s.session_id
        with (
            patch.object(Session, "_redact_dict", side_effect=RuntimeError("boom")),
            caplog.at_level(logging.WARNING, logger="capsule"),
        ):
            from capsule_trace.core.models import Event

            event = Event(
                session_id=s.session_id,
                step_index=s.next_step_index(),
                event_type=EventType.TOOL_CALL,
                payload={"tool_name": "x", "arguments": {}},
            )
            s.capture_event(event)

    assert any("redact" in rec.message.lower() for rec in caplog.records)
    events = in_memory_backend.read_events(session_id)
    assert len(events) == 1


# ── Thread context propagation (P1) ──────────────────────────


def test_wrap_executor_propagates_session_to_threads(in_memory_backend):
    """P1: ThreadPoolExecutor doesn't inherit ContextVars by default — the
    most common agent pattern (parallel tool calls) used to silently record
    zero events. wrap_executor() must fix that."""
    from concurrent.futures import ThreadPoolExecutor

    from capsule_trace.core.context import get_current_session
    from capsule_trace.core.models import Event

    def _record_from_thread(i: int) -> str:
        session = get_current_session()
        assert session is not None, "thread did not inherit the active session"
        event = Event(
            session_id=session.session_id,
            step_index=session.next_step_index(),
            event_type=EventType.TOOL_CALL,
            payload={"tool_name": f"thread-{i}", "arguments": {}},
        )
        session.capture_event(event)
        return f"done-{i}"

    with Session(agent_name="thread-test", storage_backend=in_memory_backend) as s:
        session_id = s.session_id
        with s.wrap_executor(ThreadPoolExecutor(max_workers=3)) as pool:
            results = list(pool.map(_record_from_thread, range(3)))

    assert sorted(results) == ["done-0", "done-1", "done-2"]
    events = in_memory_backend.read_events(session_id)
    assert len(events) == 3
    tool_names = {
        (e.payload if isinstance(e.payload, dict) else e.payload.model_dump())["tool_name"]
        for e in events
    }
    assert tool_names == {"thread-0", "thread-1", "thread-2"}


def test_unwrapped_executor_loses_thread_events(in_memory_backend):
    """Sanity check for the bug wrap_executor fixes: without it, a thread
    genuinely sees no active session."""
    from concurrent.futures import ThreadPoolExecutor

    from capsule_trace.core.context import get_current_session

    with (
        Session(agent_name="unwrapped-thread-test", storage_backend=in_memory_backend),
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        seen = pool.submit(get_current_session).result()

    assert seen is None


def test_finalize_warns_on_zero_events_after_meaningful_duration(in_memory_backend, caplog):
    import logging
    import time

    with (
        caplog.at_level(logging.WARNING, logger="capsule"),
        Session(agent_name="silent-thread-loss", storage_backend=in_memory_backend),
    ):
        time.sleep(0.06)  # exceed _ZERO_EVENTS_WARNING_THRESHOLD_MS (50ms)

    assert any("zero events" in rec.message for rec in caplog.records)


def test_finalize_does_not_warn_for_genuinely_trivial_session(in_memory_backend, caplog):
    import logging

    with (
        caplog.at_level(logging.WARNING, logger="capsule"),
        Session(agent_name="trivial", storage_backend=in_memory_backend),
    ):
        pass  # near-instant, zero events — not suspicious

    assert not any("zero events" in rec.message for rec in caplog.records)


# ── SQLite concurrency (P1) ───────────────────────────────────


def test_sqlite_backend_sets_wal_and_busy_timeout(tmp_path):
    """P1 regression guard: without these PRAGMAs, a concurrent writer can
    hit "database is locked" immediately, which capture_event()'s catch-all
    swallows — silent event loss. This is the deterministic check; the
    ThreadPoolExecutor test below exercises the real end-to-end path but
    (like most lock-contention bugs) isn't guaranteed to reproduce the race
    on every machine."""
    from sqlalchemy import text

    backend = SQLiteBackend(tmp_path / "pragma-check.db")
    with backend._Session() as db:
        journal_mode = db.execute(text("PRAGMA journal_mode")).scalar()
        busy_timeout = db.execute(text("PRAGMA busy_timeout")).scalar()

    assert journal_mode == "wal"
    assert busy_timeout == 5000


def test_concurrent_sessions_writing_events_lose_nothing(tmp_path):
    """P1: without WAL + busy_timeout, concurrent writers to the same
    SQLite file raise "database is locked", which capture_event() swallows
    — events vanish silently. All 5 sessions' events must survive.

    The backend is created once up front (schema + WAL setup happens a
    single time, same as check_same_thread=False is designed for: one
    engine/connection pool shared across threads) — five sessions then
    write through it concurrently.
    """
    from concurrent.futures import ThreadPoolExecutor

    from capsule_trace.core.models import Event

    backend = SQLiteBackend(tmp_path / "concurrent.db")

    def _run_session(i: int) -> str:
        with Session(agent_name=f"concurrent-{i}", storage_backend=backend) as s:
            for step in range(10):
                event = Event(
                    session_id=s.session_id,
                    step_index=s.next_step_index(),
                    event_type=EventType.TOOL_CALL,
                    payload={"tool_name": f"step-{step}", "arguments": {}},
                )
                s.capture_event(event)
            return s.session_id

    with ThreadPoolExecutor(max_workers=5) as pool:
        session_ids = list(pool.map(_run_session, range(5)))

    assert len(set(session_ids)) == 5
    for session_id in session_ids:
        events = backend.read_events(session_id)
        assert len(events) == 10, f"session {session_id} lost events under concurrency"


# ── Crash recovery (P1) ───────────────────────────────────────


def test_session_row_exists_immediately_after_enter(in_memory_backend):
    """Even before any events are captured or finalize() runs, the session
    must already be listable — this is what makes a hard-killed run
    (SIGKILL, OOM-kill; atexit cannot help with those) still recoverable."""
    s = Session(agent_name="crash-test", storage_backend=in_memory_backend)
    s.__enter__()
    try:
        meta = in_memory_backend.read_session_metadata(s.session_id)
        assert meta.status == SessionStatus.IN_PROGRESS
    finally:
        s.finalize(status=SessionStatus.CANCELLED)


def test_atexit_hook_finalizes_sessions_never_exited(in_memory_backend):
    """Simulates a crash: __enter__() runs, __exit__() never does (the
    scenario a SIGKILL or an unexpected os._exit() produces). The atexit
    hook — called directly here rather than by an actual process exit —
    must finalize it so it's listable instead of stuck in_progress forever."""
    from capsule_trace.core.models import Event
    from capsule_trace.core.session import _finalize_open_sessions_at_exit, _open_sessions

    s = Session(agent_name="crashed-agent", storage_backend=in_memory_backend)
    s.__enter__()
    session_id = s.session_id

    event = Event(
        session_id=session_id,
        step_index=s.next_step_index(),
        event_type=EventType.TOOL_CALL,
        payload={"tool_name": "did_some_work", "arguments": {}},
    )
    s.capture_event(event)

    assert s in _open_sessions

    # __exit__ deliberately never called — simulate the process exiting
    # without it by invoking the atexit hook directly.
    _finalize_open_sessions_at_exit()

    assert s not in _open_sessions
    meta = in_memory_backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.CANCELLED

    listed_ids = [m.session_id for m in in_memory_backend.list_sessions()]
    assert session_id in listed_ids


def test_crashed_session_is_exportable(tmp_path):
    """Full round-trip: crash before __exit__, atexit-recover, export."""
    from capsule_trace.core.exporter import export_capsule
    from capsule_trace.core.models import Event
    from capsule_trace.core.session import _finalize_open_sessions_at_exit

    backend = SQLiteBackend(tmp_path / "crash.db")
    s = Session(agent_name="crashed-and-exported", storage_backend=backend)
    s.__enter__()
    session_id = s.session_id
    s.capture_event(
        Event(
            session_id=session_id,
            step_index=s.next_step_index(),
            event_type=EventType.TOOL_CALL,
            payload={"tool_name": "work", "arguments": {}},
        )
    )

    _finalize_open_sessions_at_exit()

    out_path = tmp_path / "crashed.capsule"
    result = export_capsule(session_id, backend, out_path)
    assert result.exists()
    assert result.stat().st_size > 0


def test_export_reconstructs_metadata_when_session_row_missing(tmp_path):
    """Events captured without ever using the Session context manager (no
    __enter__, so no row is written) must still be exportable instead of
    raising KeyError."""
    from capsule_trace.core.exporter import export_capsule
    from capsule_trace.core.models import Event

    backend = SQLiteBackend(tmp_path / "no_row.db")
    session_id = "orphaned-session"
    backend.write_event(
        Event(
            session_id=session_id,
            step_index=0,
            event_type=EventType.TOOL_CALL,
            payload={"tool_name": "orphan_work", "arguments": {}},
        )
    )

    out_path = tmp_path / "orphaned.capsule"
    result = export_capsule(session_id, backend, out_path)
    assert result.exists()


def test_export_still_raises_when_both_session_and_events_missing(tmp_path):
    """The KeyError fallback only applies when there's something to
    reconstruct from — a genuinely nonexistent session must still raise."""
    from capsule_trace.core.exporter import export_capsule

    backend = SQLiteBackend(tmp_path / "empty.db")
    with pytest.raises(KeyError):
        export_capsule("never-existed", backend, tmp_path / "out.capsule")
