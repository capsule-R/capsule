"""Anthropic SDK integration — patches messages.create (sync + async)."""

from __future__ import annotations

import functools
import logging
import time
import uuid
from typing import Any

from capsule_trace.core.context import get_current_session
from capsule_trace.core.models import (
    EventType,
    LLMCallPayload,
    LLMMessage,
    LLMParameters,
    LLMResponse,
    LLMUsage,
)

logger = logging.getLogger("capsule.integrations.anthropic")

_PATCHED = False


def patch() -> None:
    """Monkey-patch anthropic.Anthropic and anthropic.AsyncAnthropic."""
    global _PATCHED
    if _PATCHED:
        return

    try:
        import anthropic  # type: ignore[import-untyped]
    except ImportError:
        return

    _patch_sync_client(anthropic)
    _patch_async_client(anthropic)
    _PATCHED = True
    logger.debug("capsule: Anthropic SDK patched")


def _patch_sync_client(anthropic: Any) -> None:
    original = anthropic.resources.messages.Messages.create

    @functools.wraps(original)
    def patched_create(self: Any, **kwargs: Any) -> Any:
        session = get_current_session()
        if session is None:
            return original(self, **kwargs)

        payload = _build_request_payload(kwargs)
        start = time.perf_counter()
        try:
            response = original(self, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            payload = _complete_payload(payload, response, duration)
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _emit_event(session, payload, duration)
            raise

    anthropic.resources.messages.Messages.create = patched_create


def _patch_async_client(anthropic: Any) -> None:
    original = anthropic.resources.messages.AsyncMessages.create

    @functools.wraps(original)
    async def patched_async_create(self: Any, **kwargs: Any) -> Any:
        session = get_current_session()
        if session is None:
            return await original(self, **kwargs)

        payload = _build_request_payload(kwargs)
        start = time.perf_counter()
        try:
            response = await original(self, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            payload = _complete_payload(payload, response, duration)
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _emit_event(session, payload, duration)
            raise

    anthropic.resources.messages.AsyncMessages.create = patched_async_create


def _build_request_payload(kwargs: dict[str, Any]) -> LLMCallPayload:
    messages = [
        LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
        for m in kwargs.get("messages", [])
    ]
    params = LLMParameters(
        temperature=kwargs.get("temperature"),
        top_p=kwargs.get("top_p"),
        max_tokens=kwargs.get("max_tokens"),
    )
    return LLMCallPayload(
        provider="anthropic",
        model=kwargs.get("model", "unknown"),
        parameters=params,
        messages=messages,
    )


def _complete_payload(
    payload: LLMCallPayload, response: Any, duration_ms: float
) -> LLMCallPayload:
    try:
        content_text: str | None = None
        tool_calls: list[Any] = []

        for block in response.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "type": "tool_use",
                        "name": block.name,
                        "input": block.input,
                    }
                )

        usage = response.usage
        payload.response = LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage=LLMUsage(
                prompt_tokens=usage.input_tokens if usage else 0,
                completion_tokens=usage.output_tokens if usage else 0,
                total_tokens=(usage.input_tokens + usage.output_tokens) if usage else 0,
            ),
        )

        cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
        payload.cassette_ref = f"cassettes/{cassette_id}.json"
    except Exception:
        logger.debug("capsule: failed to extract Anthropic response", exc_info=True)

    return payload


def _emit_event(session: Any, payload: LLMCallPayload, duration_ms: float) -> None:
    from capsule_trace.core.models import Event

    event = Event(
        session_id=session.session_id,
        step_index=session.next_step_index(),
        event_type=EventType.LLM_CALL,
        duration_ms=duration_ms,
        payload=payload,
    )
    session.capture_event(event)
