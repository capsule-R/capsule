"""Unit tests for the LangChain callback handler."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from capsule_trace.core.models import EventType
from capsule_trace.core.session import Session
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture()
def backend(tmp_path):
    return SQLiteBackend(tmp_path / "test.db")


def _make_llm_result(content: str = "Hello", model: str = "gpt-4o") -> MagicMock:
    result = MagicMock()
    gen = MagicMock()
    gen.text = content
    result.generations = [[gen]]
    result.llm_output = {
        "model_name": model,
        "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    return result


def test_callback_handler_captures_llm_call(backend):
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler

    handler = CapsuleCallbackHandler()
    run_id = uuid4()

    with Session(agent_name="langchain-test", storage_backend=backend) as s:
        sid = s.session_id
        handler.on_chat_model_start({}, [[]], run_id=run_id)
        handler.on_llm_end(_make_llm_result("World"), run_id=run_id)

    events = backend.read_events(sid)
    assert len(events) == 1
    assert events[0].event_type == EventType.LLM_CALL
    payload = events[0].payload
    resp = payload.get("response") if isinstance(payload, dict) else None
    if resp:
        assert resp.get("content") == "World"


def test_callback_handler_captures_tool_call(backend):
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler

    handler = CapsuleCallbackHandler()
    run_id = uuid4()

    with Session(agent_name="langchain-tool-test", storage_backend=backend) as s:
        sid = s.session_id
        handler.on_tool_start({}, "get_balance", run_id=run_id)
        handler.on_tool_end('{"balance": 1500}', run_id=run_id, name="get_balance", input="cust_001")

    events = backend.read_events(sid)
    assert len(events) == 1
    assert events[0].event_type == EventType.TOOL_CALL


def test_callback_handler_no_session_no_error(backend):
    """Handler gracefully does nothing when no session is active."""
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler

    handler = CapsuleCallbackHandler()
    run_id = uuid4()
    # No Session context — should not raise
    handler.on_chat_model_start({}, [[]], run_id=run_id)
    handler.on_llm_end(_make_llm_result(), run_id=run_id)


def test_callback_handler_error_cleans_up(backend):
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler

    handler = CapsuleCallbackHandler()
    run_id = uuid4()
    handler.on_chat_model_start({}, [[]], run_id=run_id)
    assert run_id in handler._call_start_times
    handler.on_llm_error(RuntimeError("API down"), run_id=run_id)
    assert run_id not in handler._call_start_times


def test_multiple_llm_calls_sequential(backend):
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler

    handler = CapsuleCallbackHandler()

    with Session(agent_name="multi-llm", storage_backend=backend) as s:
        sid = s.session_id
        for i in range(3):
            rid = uuid4()
            handler.on_chat_model_start({}, [[]], run_id=rid)
            handler.on_llm_end(_make_llm_result(f"response {i}"), run_id=rid)

    events = backend.read_events(sid)
    assert len(events) == 3
    assert [e.step_index for e in events] == [0, 1, 2]
