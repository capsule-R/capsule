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
        with patch.object(
            Session, "_redact_dict", side_effect=RuntimeError("boom")
        ), caplog.at_level(logging.WARNING, logger="capsule"):
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
