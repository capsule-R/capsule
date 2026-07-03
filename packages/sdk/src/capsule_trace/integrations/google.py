"""Google Generative AI integration — patches generate_content (sync + async)."""

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
)
from capsule_trace.replay.cassette import CassetteMissError, compute_request_hash

logger = logging.getLogger("capsule.integrations.google")

_PATCHED = False


def patch() -> None:
    global _PATCHED
    if _PATCHED:
        return

    try:
        import google.generativeai as genai
    except ImportError:
        return

    _patch_generate_content(genai)
    _PATCHED = True
    logger.debug("capsule: Google Generative AI SDK patched")


def _patch_generate_content(genai: Any) -> None:
    original = genai.GenerativeModel.generate_content

    @functools.wraps(original)
    def patched(self: Any, contents: Any, **kwargs: Any) -> Any:
        from capsule_trace.replay.mode import get_replay_store

        store = get_replay_store()
        if store is not None:
            return _cassette_response_google(store, self, contents, kwargs)

        session = get_current_session()
        if session is None:
            return original(self, contents, **kwargs)

        model_name = getattr(self, "model_name", "gemini")
        payload = LLMCallPayload(
            provider="google",
            model=model_name,
            parameters=LLMParameters(
                temperature=kwargs.get("generation_config", {}).get("temperature"),
                max_tokens=kwargs.get("generation_config", {}).get("max_output_tokens"),
            ),
            messages=[LLMMessage(role="user", content=str(contents))],
        )
        start = time.perf_counter()
        try:
            response = original(self, contents, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            try:
                payload.response = LLMResponse(
                    content=response.text,
                    finish_reason=str(response.candidates[0].finish_reason)
                    if response.candidates
                    else None,
                )
                cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
                session.write_cassette(
                    cassette_id,
                    {
                        "request_hash": _google_request_hash(model_name, contents, kwargs),
                        "request": {"contents": str(contents), **kwargs},
                        "raw_response": _to_raw_dict(response),
                        "model": payload.model,
                    },
                )
                payload.cassette_ref = f"cassettes/{cassette_id}.json"
            except Exception:
                pass
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _write_error_cassette(session, payload, exc, contents, kwargs)
            _emit_event(session, payload, duration)
            raise

    genai.GenerativeModel.generate_content = patched


def _to_raw_dict(response: Any) -> Any:
    """Best-effort serialization of a Google Generative AI response to a plain dict."""
    if hasattr(response, "to_dict"):
        try:
            return response.to_dict()
        except Exception:
            pass
    try:
        return {
            "text": response.text,
            "candidates": [
                {"finish_reason": str(c.finish_reason)} for c in (response.candidates or [])
            ],
        }
    except Exception:
        return {"repr": repr(response)}


def _write_error_cassette(
    session: Any, payload: LLMCallPayload, exc: Exception, contents: Any, kwargs: dict[str, Any]
) -> None:
    """Record a failed call so replay can reproduce the failure, not just successes."""
    try:
        cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
        session.write_cassette(
            cassette_id,
            {
                "request_hash": _google_request_hash(payload.model, contents, kwargs),
                "request": {"contents": str(contents), **kwargs},
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "model": payload.model,
            },
        )
        payload.cassette_ref = f"cassettes/{cassette_id}.json"
    except Exception:
        logger.debug("capsule: failed to write error cassette", exc_info=True)


def _google_request_hash(model: str, contents: Any, kwargs: dict[str, Any]) -> str:
    generation_config = kwargs.get("generation_config", {})
    if not isinstance(generation_config, dict):
        generation_config = {}
    return compute_request_hash(
        model=model,
        messages=[{"role": "user", "content": str(contents)}],
        temperature=generation_config.get("temperature"),
        max_tokens=generation_config.get("max_output_tokens"),
    )


def _cassette_response_google(store: Any, client: Any, contents: Any, kwargs: dict[str, Any]) -> Any:
    """Return a mock Google Generative AI response matching this exact request.

    Without this, Google calls during "replay" hit the live API with real
    keys — costing money and breaking determinism, since only the OpenAI
    integration checked get_replay_store() before this fix.
    """
    from unittest.mock import MagicMock

    model_name = getattr(client, "model_name", "gemini")
    request_hash = _google_request_hash(model_name, contents, kwargs)
    cassette_data = store.get_by_request_hash(request_hash)
    if cassette_data is None:
        raise CassetteMissError(
            f"capsule: no cassette recorded for this request (model={model_name!r}) "
            "— the replayed call diverges from what was recorded"
        )
    if "error" in cassette_data:
        raise RuntimeError(cassette_data["error"])

    raw = cassette_data.get("raw_response", cassette_data)
    mock_resp = MagicMock()
    mock_resp.text = raw.get("text") if isinstance(raw, dict) else None
    candidates = raw.get("candidates", []) if isinstance(raw, dict) else []
    mock_candidates = []
    for c in candidates:
        mock_c = MagicMock()
        mock_c.finish_reason = c.get("finish_reason")
        mock_candidates.append(mock_c)
    mock_resp.candidates = mock_candidates
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
