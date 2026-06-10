"""Unit tests for tool call capture."""

from __future__ import annotations

import pytest

from capsule_trace.core.models import EventType, SessionStatus
from capsule_trace.core.session import Session
from capsule_trace.integrations.tools import capture_tool_call
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture()
def backend(tmp_path):
    return SQLiteBackend(tmp_path / "test.db")


def test_capture_tool_call_decorator(backend):
    @capture_tool_call(tool_name="get_balance", tool_namespace="billing")
    def get_balance(customer_id: str) -> dict:
        return {"balance": 1500.0}

    with Session(agent_name="tool-test", storage_backend=backend) as s:
        sid = s.session_id
        result = get_balance("cust_001")

    assert result == {"balance": 1500.0}
    events = backend.read_events(sid)
    assert len(events) == 1
    assert events[0].event_type == EventType.TOOL_CALL
    payload = events[0].payload
    args = payload.get("arguments") if isinstance(payload, dict) else payload.arguments
    assert args.get("customer_id") == "cust_001"


def test_capture_tool_call_captures_error(backend):
    @capture_tool_call(tool_name="failing_tool")
    def failing_tool() -> None:
        raise ValueError("tool exploded")

    with pytest.raises(ValueError):
        with Session(agent_name="error-tool-test", storage_backend=backend) as s:
            sid = s.session_id
            failing_tool()

    events = backend.read_events(sid)
    assert len(events) == 1
    payload = events[0].payload
    error = payload.get("error") if isinstance(payload, dict) else payload.error
    assert error is not None
    assert "ValueError" in error


def test_capture_tool_call_no_session():
    """When no session is active, the tool runs normally with zero side effects."""
    @capture_tool_call(tool_name="passthrough")
    def passthrough(x: int) -> int:
        return x * 2

    assert passthrough(5) == 10


def test_multiple_tool_calls_step_order(backend):
    @capture_tool_call(tool_name="tool_a")
    def tool_a() -> str:
        return "a"

    @capture_tool_call(tool_name="tool_b")
    def tool_b() -> str:
        return "b"

    with Session(agent_name="multi-tool", storage_backend=backend) as s:
        sid = s.session_id
        tool_a()
        tool_b()

    events = backend.read_events(sid)
    assert len(events) == 2
    assert events[0].step_index == 0
    assert events[1].step_index == 1

    def tool_name(p):
        return p.get("tool_name") if isinstance(p, dict) else p.tool_name

    assert tool_name(events[0].payload) == "tool_a"
    assert tool_name(events[1].payload) == "tool_b"


def test_capture_tool_call_with_complex_args(backend):
    @capture_tool_call(tool_name="complex_args")
    def complex_fn(user: dict, tags: list, flag: bool = True) -> str:
        return "ok"

    with Session(agent_name="complex-arg-test", storage_backend=backend) as s:
        sid = s.session_id
        complex_fn({"id": 1}, ["a", "b"], flag=False)

    events = backend.read_events(sid)
    payload = events[0].payload
    args = payload.get("arguments") if isinstance(payload, dict) else payload.arguments
    assert args["user"] == {"id": 1}
    assert args["tags"] == ["a", "b"]
    assert args["flag"] is False


@pytest.mark.asyncio
async def test_capture_tool_call_inside_async_session(backend):
    @capture_tool_call(tool_name="async_tool")
    def sync_tool_in_async() -> int:
        return 99

    async with Session(agent_name="async-tool-test", storage_backend=backend) as s:
        sid = s.session_id
        result = sync_tool_in_async()

    assert result == 99
    events = backend.read_events(sid)
    assert len(events) == 1
    assert events[0].event_type == EventType.TOOL_CALL
