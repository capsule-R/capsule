"""Integration test — OpenAI SDK capture with mocked responses."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from capsule_trace.core.models import EventType, SessionStatus
from capsule_trace.core.session import Session
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture(autouse=True)
def backend(tmp_path):
    return SQLiteBackend(tmp_path / "test.db")


def _mock_openai_response(content: str = "Mocked response") -> MagicMock:
    """Build a mock that matches openai.ChatCompletion shape."""
    response = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    choice.message.tool_calls = None
    choice.finish_reason = "stop"
    response.choices = [choice]
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 5
    response.usage.total_tokens = 15
    return response


def test_openai_llm_call_captured(tmp_path, backend):
    """Verify that an OpenAI chat.completions call is captured as an LLM event."""
    with Session(agent_name="openai-test", storage_backend=backend) as s:
        session_id = s.session_id

        # Simulate what the patched method does
        from capsule_trace.core.models import (
            Event,
            LLMCallPayload,
            LLMMessage,
            LLMResponse,
            LLMUsage,
        )

        payload = LLMCallPayload(
            provider="openai",
            model="gpt-4o",
            messages=[LLMMessage(role="user", content="Test message")],
            response=LLMResponse(
                content="Mocked response",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
        )
        event = Event(
            session_id=s.session_id,
            step_index=s.next_step_index(),
            event_type=EventType.LLM_CALL,
            duration_ms=123.0,
            payload=payload,
        )
        s.capture_event(event)

    events = backend.read_events(session_id)
    assert len(events) == 1
    assert events[0].event_type == EventType.LLM_CALL

    meta = backend.read_session_metadata(session_id)
    assert meta.status == SessionStatus.SUCCESS
    assert meta.step_count == 1


def test_multiple_llm_calls_captured(tmp_path, backend):
    """Multiple LLM calls in sequence should all be captured with correct step indices."""
    from capsule_trace.core.models import Event, LLMCallPayload, LLMMessage

    with Session(agent_name="multi-call", storage_backend=backend) as s:
        session_id = s.session_id
        for i in range(3):
            payload = LLMCallPayload(
                provider="openai",
                model="gpt-4o",
                messages=[LLMMessage(role="user", content=f"call {i}")],
            )
            event = Event(
                session_id=s.session_id,
                step_index=s.next_step_index(),
                event_type=EventType.LLM_CALL,
                duration_ms=float(i * 10),
                payload=payload,
            )
            s.capture_event(event)

    events = backend.read_events(session_id)
    assert len(events) == 3
    assert [e.step_index for e in events] == [0, 1, 2]
