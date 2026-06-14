"""Unit tests for Pydantic data models."""

from __future__ import annotations

from capsule_trace.core.models import (
    CapsuleManifest,
    Event,
    EventType,
    LLMCallPayload,
    LLMMessage,
    LLMParameters,
    LLMResponse,
    LLMUsage,
    MemoryPayload,
    MemoryType,
    SessionMetadata,
    SessionStatus,
    ToolCallPayload,
)


def test_event_has_auto_id():
    e = Event(
        session_id="ses_001",
        step_index=0,
        event_type=EventType.USER_MESSAGE,
        payload={"text": "hello"},
    )
    assert e.event_id != ""
    assert e.timestamp is not None


def test_llm_call_payload_roundtrip():
    payload = LLMCallPayload(
        provider="openai",
        model="gpt-4o",
        parameters=LLMParameters(temperature=0.7, max_tokens=512),
        messages=[LLMMessage(role="user", content="Hello")],
        response=LLMResponse(
            content="Hi there",
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ),
    )
    dumped = payload.model_dump(mode="json")
    restored = LLMCallPayload(**dumped)
    assert restored.model == "gpt-4o"
    assert restored.response is not None
    assert restored.response.content == "Hi there"
    assert restored.response.usage.total_tokens == 15


def test_tool_call_payload():
    payload = ToolCallPayload(
        tool_name="get_balance",
        arguments={"customer_id": "cust_001"},
        result={"balance": 1500.0},
        execution_duration_ms=42.5,
    )
    assert payload.error is None
    d = payload.model_dump(mode="json")
    assert d["tool_name"] == "get_balance"


def test_memory_payload_defaults():
    p = MemoryPayload(key="intent", value="refund")
    assert p.memory_type == MemoryType.CUSTOM
    assert p.value_type == "string"


def test_session_metadata_defaults():
    meta = SessionMetadata(session_id="ses_001", agent_name="test")
    assert meta.status == SessionStatus.IN_PROGRESS
    assert meta.step_count == 0
    assert meta.tags == []


def test_manifest_integrity_hashes_empty_by_default():
    m = CapsuleManifest(session_id="ses_001")
    assert m.integrity.events_hash == ""
    assert m.compression.algorithm == "zstd"
    assert m.producer.sdk_name == "capsule-python"


def test_event_model_dump_json_safe():
    payload = LLMCallPayload(
        provider="anthropic",
        model="claude-sonnet-4-6",
        messages=[LLMMessage(role="user", content="hello")],
    )
    event = Event(
        session_id="ses_001",
        step_index=1,
        event_type=EventType.LLM_CALL,
        payload=payload,
    )
    data = event.model_dump_json_safe()
    assert data["event_type"] == "llm_call"
    assert "payload" in data
