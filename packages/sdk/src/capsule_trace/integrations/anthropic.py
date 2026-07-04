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
from capsule_trace.replay.cassette import CassetteMissError, compute_request_hash

logger = logging.getLogger("capsule.integrations.anthropic")

_PATCHED = False


def patch() -> None:
    """Monkey-patch anthropic.Anthropic and anthropic.AsyncAnthropic."""
    global _PATCHED
    if _PATCHED:
        return

    try:
        import anthropic
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
        from capsule_trace.replay.mode import get_replay_store

        store = get_replay_store()
        if store is not None:
            return _cassette_response_anthropic(store, kwargs)

        session = get_current_session()
        if session is None:
            return original(self, **kwargs)

        payload = _build_request_payload(kwargs)
        start = time.perf_counter()
        try:
            response = original(self, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            payload = _complete_payload(payload, response, duration, session, kwargs)
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _write_error_cassette(session, payload, exc, kwargs)
            _emit_event(session, payload, duration)
            raise

    anthropic.resources.messages.Messages.create = patched_create


def _patch_async_client(anthropic: Any) -> None:
    original = anthropic.resources.messages.AsyncMessages.create

    @functools.wraps(original)
    async def patched_async_create(self: Any, **kwargs: Any) -> Any:
        from capsule_trace.replay.mode import get_replay_store

        store = get_replay_store()
        if store is not None:
            return _cassette_response_anthropic(store, kwargs)

        session = get_current_session()
        if session is None:
            return await original(self, **kwargs)

        payload = _build_request_payload(kwargs)
        start = time.perf_counter()
        try:
            response = await original(self, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            payload = _complete_payload(payload, response, duration, session, kwargs)
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _write_error_cassette(session, payload, exc, kwargs)
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
    payload: LLMCallPayload,
    response: Any,
    duration_ms: float,
    session: Any = None,
    request_kwargs: dict[str, Any] | None = None,
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
        if session is not None:
            kwargs = request_kwargs or {}
            session.write_cassette(
                cassette_id,
                {
                    "request_hash": compute_request_hash(
                        model=payload.model,
                        messages=kwargs.get("messages", []),
                        temperature=kwargs.get("temperature"),
                        max_tokens=kwargs.get("max_tokens"),
                    ),
                    "request": kwargs,
                    "raw_response": _to_raw_dict(response),
                    "model": payload.model,
                },
            )
        payload.cassette_ref = f"cassettes/{cassette_id}.json"
    except Exception:
        logger.debug("capsule: failed to extract Anthropic response", exc_info=True)

    return payload


def _to_raw_dict(response: Any) -> Any:
    """Best-effort serialization of an Anthropic SDK response to a plain dict."""
    if hasattr(response, "model_dump"):
        try:
            return response.model_dump(mode="json")
        except Exception:
            pass
    try:
        return dict(response)
    except Exception:
        return {"repr": repr(response)}


def _write_error_cassette(
    session: Any, payload: LLMCallPayload, exc: Exception, request_kwargs: dict[str, Any]
) -> None:
    """Record a failed call so replay can reproduce the failure, not just successes."""
    try:
        cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
        session.write_cassette(
            cassette_id,
            {
                "request_hash": compute_request_hash(
                    model=payload.model,
                    messages=request_kwargs.get("messages", []),
                    temperature=request_kwargs.get("temperature"),
                    max_tokens=request_kwargs.get("max_tokens"),
                ),
                "request": request_kwargs,
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "model": payload.model,
            },
        )
        payload.cassette_ref = f"cassettes/{cassette_id}.json"
    except Exception:
        logger.debug("capsule: failed to write error cassette", exc_info=True)


def _cassette_response_anthropic(store: Any, kwargs: dict[str, Any]) -> Any:
    """Return a mock Anthropic response matching this exact request.

    Without this, Anthropic calls during "replay" hit the live API with
    real keys — costing money and breaking determinism, since only the
    OpenAI integration checked get_replay_store() before this fix.
    """
    from unittest.mock import MagicMock

    request_hash = compute_request_hash(
        model=kwargs.get("model", "unknown"),
        messages=kwargs.get("messages", []),
        temperature=kwargs.get("temperature"),
        max_tokens=kwargs.get("max_tokens"),
    )
    cassette_data = store.get_by_request_hash(request_hash)
    if cassette_data is None:
        raise CassetteMissError(
            f"capsule: no cassette recorded for this request (model={kwargs.get('model')!r}) "
            "— the replayed call diverges from what was recorded"
        )
    if "error" in cassette_data:
        raise RuntimeError(cassette_data["error"])

    raw = cassette_data.get("raw_response", cassette_data)
    mock_resp = MagicMock()
    mock_resp.content = []
    if isinstance(raw, dict) and raw.get("content"):
        for block in raw["content"]:
            mock_block = MagicMock()
            mock_block.type = block.get("type", "text")
            mock_block.text = block.get("text")
            mock_resp.content.append(mock_block)
    mock_resp.stop_reason = (
        raw.get("stop_reason", "end_turn") if isinstance(raw, dict) else "end_turn"
    )
    mock_resp.usage = MagicMock()
    usage = raw.get("usage", {}) if isinstance(raw, dict) else {}
    mock_resp.usage.input_tokens = usage.get("input_tokens", 0)
    mock_resp.usage.output_tokens = usage.get("output_tokens", 0)
    return mock_resp


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
