"""OpenAI SDK integration — patches chat.completions and responses API."""

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

logger = logging.getLogger("capsule.integrations.openai")

_PATCHED = False


def patch() -> None:
    """Monkey-patch openai.OpenAI and openai.AsyncOpenAI. Safe to call multiple times."""
    global _PATCHED
    if _PATCHED:
        return

    try:
        import openai
    except ImportError:
        return

    _patch_sync_client(openai)
    _patch_async_client(openai)
    _PATCHED = True
    logger.debug("capsule: OpenAI SDK patched")


# ── Data descriptors ──────────────────────────────────────────
#
# Python's attribute-lookup order: data descriptors > instance __dict__ >
# non-data descriptors. Regular functions are non-data descriptors, so
# unittest.mock.patch.object can shadow them with an instance attribute.
#
# By making Completions.create a *data* descriptor (defines both __get__ and
# __set__), we intercept the setattr() that patch.object issues and wrap the
# replacement (mock) with our capture logic before it is ever called.


class _CapsuleSyncDescriptor:
    """Data descriptor for Completions.create."""

    def __init__(self, original_fn: Any) -> None:
        self._original = original_fn
        # keyed by id(instance) — fine for a dev/test tool
        self._overrides: dict[int, Any] = {}

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None:
            return self
        override = self._overrides.get(id(obj))
        original_bound = self._original.__get__(obj, objtype)

        @functools.wraps(self._original)
        def wrapper(**kwargs: Any) -> Any:
            from capsule_trace.replay.mode import get_replay_store

            store = get_replay_store()
            if store is not None:
                return _cassette_response_openai(store, kwargs)

            session = get_current_session()
            payload = _build_request_payload(kwargs, provider="openai")
            start = time.perf_counter()
            call_target = override if override is not None else original_bound
            try:
                response = call_target(**kwargs)
                duration = (time.perf_counter() - start) * 1000
                payload = _complete_payload(payload, response, duration)
                if session is not None:
                    _emit_event(session, payload, duration)
                return response
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                payload.error = str(exc)
                if session is not None:
                    _emit_event(session, payload, duration)
                raise

        wrapper._capsule_wrapper = True  # type: ignore[attr-defined]
        return wrapper

    def __set__(self, obj: Any, value: Any) -> None:
        if getattr(value, "_capsule_wrapper", None) is True:
            # patch.object is restoring our own wrapper on exit — clear override
            self._overrides.pop(id(obj), None)
        else:
            # patch.object is installing a mock — store it; __get__ will wrap it
            self._overrides[id(obj)] = value

    def __delete__(self, obj: Any) -> None:
        self._overrides.pop(id(obj), None)


class _CapsuleAsyncDescriptor:
    """Data descriptor for AsyncCompletions.create."""

    def __init__(self, original_fn: Any) -> None:
        self._original = original_fn
        self._overrides: dict[int, Any] = {}

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None:
            return self
        override = self._overrides.get(id(obj))
        original_bound = self._original.__get__(obj, objtype)

        @functools.wraps(self._original)
        async def wrapper(**kwargs: Any) -> Any:
            from capsule_trace.replay.mode import get_replay_store

            store = get_replay_store()
            if store is not None:
                return _cassette_response_openai(store, kwargs)

            session = get_current_session()
            payload = _build_request_payload(kwargs, provider="openai")
            start = time.perf_counter()
            call_target = override if override is not None else original_bound
            try:
                response = await call_target(**kwargs)
                duration = (time.perf_counter() - start) * 1000
                payload = _complete_payload(payload, response, duration)
                if session is not None:
                    _emit_event(session, payload, duration)
                return response
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                payload.error = str(exc)
                if session is not None:
                    _emit_event(session, payload, duration)
                raise

        wrapper._capsule_wrapper = True  # type: ignore[attr-defined]
        return wrapper

    def __set__(self, obj: Any, value: Any) -> None:
        if getattr(value, "_capsule_wrapper", False):
            self._overrides.pop(id(obj), None)
        else:
            self._overrides[id(obj)] = value

    def __delete__(self, obj: Any) -> None:
        self._overrides.pop(id(obj), None)


# ── Patchers ──────────────────────────────────────────────────


def _patch_sync_client(openai: Any) -> None:
    original = openai.resources.chat.completions.Completions.create
    openai.resources.chat.completions.Completions.create = _CapsuleSyncDescriptor(original)


def _patch_async_client(openai: Any) -> None:
    original = openai.resources.chat.completions.AsyncCompletions.create
    openai.resources.chat.completions.AsyncCompletions.create = _CapsuleAsyncDescriptor(original)


# ── Payload helpers ───────────────────────────────────────────


def _build_request_payload(kwargs: dict[str, Any], provider: str) -> LLMCallPayload:
    messages = [
        LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
        for m in kwargs.get("messages", [])
    ]
    params = LLMParameters(
        temperature=kwargs.get("temperature"),
        top_p=kwargs.get("top_p"),
        max_tokens=kwargs.get("max_tokens"),
        seed=kwargs.get("seed"),
        frequency_penalty=kwargs.get("frequency_penalty"),
        presence_penalty=kwargs.get("presence_penalty"),
    )
    return LLMCallPayload(
        provider=provider,
        model=kwargs.get("model", "unknown"),
        parameters=params,
        messages=messages,
    )


def _complete_payload(payload: LLMCallPayload, response: Any, duration_ms: float) -> LLMCallPayload:
    try:
        choice = response.choices[0] if response.choices else None
        usage = response.usage

        tool_calls: list[Any] = []
        if choice and choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]

        payload.response = LLMResponse(
            content=choice.message.content if choice else None,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason if choice else None,
            usage=LLMUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
        )

        cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
        payload.cassette_ref = f"cassettes/{cassette_id}.json"
    except Exception:
        logger.debug("capsule: failed to extract OpenAI response", exc_info=True)

    return payload


def _cassette_response_openai(store: Any, kwargs: dict[str, Any]) -> Any:
    """Return a mock OpenAI response object built from the next cassette entry."""
    from unittest.mock import MagicMock

    cassette_data = store._pop_next() if hasattr(store, "_pop_next") else None
    if cassette_data is None:
        raise RuntimeError("capsule: no cassette available for replay step")

    raw = cassette_data.get("raw_response", cassette_data)
    mock_resp = MagicMock()
    mock_resp.choices = []
    if isinstance(raw, dict) and raw.get("choices"):
        for c in raw["choices"]:
            choice = MagicMock()
            choice.message.content = c.get("message", {}).get("content")
            choice.message.tool_calls = None
            choice.finish_reason = c.get("finish_reason", "stop")
            mock_resp.choices.append(choice)
    mock_resp.usage = MagicMock()
    mock_resp.usage.prompt_tokens = raw.get("usage", {}).get("prompt_tokens", 0)
    mock_resp.usage.completion_tokens = raw.get("usage", {}).get("completion_tokens", 0)
    mock_resp.usage.total_tokens = raw.get("usage", {}).get("total_tokens", 0)
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
