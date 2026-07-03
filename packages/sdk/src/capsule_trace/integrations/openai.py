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
from capsule_trace.replay.cassette import CassetteMissError, compute_request_hash

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
                payload = _complete_payload(payload, response, duration, session, kwargs)
                if session is not None:
                    _emit_event(session, payload, duration)
                return response
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                payload.error = str(exc)
                if session is not None:
                    _write_error_cassette(session, payload, exc, kwargs)
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
                payload = _complete_payload(payload, response, duration, session, kwargs)
                if session is not None:
                    _emit_event(session, payload, duration)
                return response
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                payload.error = str(exc)
                if session is not None:
                    _write_error_cassette(session, payload, exc, kwargs)
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


def _complete_payload(
    payload: LLMCallPayload,
    response: Any,
    duration_ms: float,
    session: Any = None,
    request_kwargs: dict[str, Any] | None = None,
) -> LLMCallPayload:
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
        logger.debug("capsule: failed to extract OpenAI response", exc_info=True)

    return payload


def _to_raw_dict(response: Any) -> Any:
    """Best-effort serialization of an OpenAI SDK response to a plain dict."""
    if hasattr(response, "model_dump"):
        try:
            return response.model_dump(mode="json")
        except Exception:
            pass
    try:
        return dict(response)
    except Exception:
        return {"repr": repr(response)}


def _write_error_cassette(session: Any, payload: LLMCallPayload, exc: Exception, request_kwargs: dict[str, Any]) -> None:
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


def _cassette_response_openai(store: Any, kwargs: dict[str, Any]) -> Any:
    """Return a mock OpenAI response object matching this exact request.

    Matches by the canonical request hash recorded at capture time — NOT
    insertion/tar order, which is not the same as recording order and used
    to serve silently-wrong responses. A request with no matching cassette
    is a real divergence and must fail loudly, not fall back to whatever
    cassette happens to be next.
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
