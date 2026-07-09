"""Event and session data models for the .capsule format."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(UTC)


def _ulid() -> str:
    import ulid

    return str(ulid.new())


# ──────────────────────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────────────────────


class EventType(StrEnum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    ERROR = "error"
    USER_MESSAGE = "user_message"


class SessionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MemoryType(StrEnum):
    CONVERSATION = "conversation"
    RAG_CONTEXT = "rag_context"
    SCRATCHPAD = "scratchpad"
    CUSTOM = "custom"


# ──────────────────────────────────────────────────────────────
# LLM Call payload
# ──────────────────────────────────────────────────────────────


class LLMParameters(BaseModel):
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None

    model_config = {"extra": "allow"}


class LLMMessage(BaseModel):
    role: str
    content: str | list[Any] | None = None

    model_config = {"extra": "allow"}


class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    model_config = {"extra": "allow"}


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[Any] = Field(default_factory=list)
    finish_reason: str | None = None
    usage: LLMUsage = Field(default_factory=LLMUsage)

    model_config = {"extra": "allow"}


class LLMCallPayload(BaseModel):
    provider: str
    model: str
    model_version: str | None = None
    parameters: LLMParameters = Field(default_factory=LLMParameters)
    messages: list[LLMMessage] = Field(default_factory=list)
    response: LLMResponse | None = None
    error: str | None = None
    cassette_ref: str | None = None

    # protected_namespaces=() silences the pydantic warning about the `model`
    # / `model_version` fields colliding with the protected "model_" namespace.
    model_config = ConfigDict(extra="allow", protected_namespaces=())


# ──────────────────────────────────────────────────────────────
# Tool Call payload
# ──────────────────────────────────────────────────────────────


class ToolCallPayload(BaseModel):
    tool_name: str
    tool_namespace: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    error: str | None = None
    execution_duration_ms: float | None = None
    tool_version: str | None = None
    cassette_ref: str | None = None


# ──────────────────────────────────────────────────────────────
# Memory payload
# ──────────────────────────────────────────────────────────────


class MemoryPayload(BaseModel):
    memory_type: MemoryType = MemoryType.CUSTOM
    key: str
    value: Any = None
    value_type: str = "string"
    snapshot_after_ref: str | None = None


# ──────────────────────────────────────────────────────────────
# Error payload
# ──────────────────────────────────────────────────────────────


class ErrorPayload(BaseModel):
    error_type: str
    error_message: str
    stack_trace: str | None = None
    is_fatal: bool = True


# ──────────────────────────────────────────────────────────────
# Base event
# ──────────────────────────────────────────────────────────────


class Event(BaseModel):
    event_id: str = Field(default_factory=_ulid)
    session_id: str
    step_index: int
    parent_event_id: str | None = None
    event_type: EventType
    timestamp: datetime = Field(default_factory=_now)
    duration_ms: float = 0.0
    payload: LLMCallPayload | ToolCallPayload | MemoryPayload | ErrorPayload | dict[str, Any]

    model_config = {"arbitrary_types_allowed": True}

    def model_dump_json_safe(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        return self.model_dump(mode="json")


# ──────────────────────────────────────────────────────────────
# Session metadata
# ──────────────────────────────────────────────────────────────


class SessionError(BaseModel):
    type: str
    message: str
    stack_trace: str | None = None


class TokenUsage(BaseModel):
    input: int = 0
    output: int = 0


class SessionMetadata(BaseModel):
    session_id: str
    agent_name: str
    agent_version: str | None = None
    started_at: datetime = Field(default_factory=_now)
    ended_at: datetime | None = None
    duration_ms: float | None = None
    status: SessionStatus = SessionStatus.IN_PROGRESS
    error: SessionError | None = None
    tags: list[str] = Field(default_factory=list)
    user_metadata: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    total_cost_usd: float = 0.0


# ──────────────────────────────────────────────────────────────
# Manifest
# ──────────────────────────────────────────────────────────────


class CapsuleIntegrity(BaseModel):
    algorithm: Literal["sha256"] = "sha256"
    events_hash: str = ""
    cassettes_hash: str = ""
    snapshots_hash: str = ""


class CapsuleEncryption(BaseModel):
    enabled: bool = False
    algorithm: str | None = None
    key_hint: str | None = None


class CapsuleCompression(BaseModel):
    algorithm: Literal["zstd"] = "zstd"
    level: int = 3


class CapsuleProducer(BaseModel):
    sdk_name: str = "capsule-python"
    sdk_version: str = "0.1.0"
    platform: str = ""
    python_version: str = ""


class CapsuleManifest(BaseModel):
    capsule_version: str = "1.0"
    format_spec_url: str = "https://capsule-five-delta.vercel.app/spec/v1.0"
    created_at: datetime = Field(default_factory=_now)
    session_id: str = ""
    integrity: CapsuleIntegrity = Field(default_factory=CapsuleIntegrity)
    encryption: CapsuleEncryption = Field(default_factory=CapsuleEncryption)
    compression: CapsuleCompression = Field(default_factory=CapsuleCompression)
    producer: CapsuleProducer = Field(default_factory=CapsuleProducer)
