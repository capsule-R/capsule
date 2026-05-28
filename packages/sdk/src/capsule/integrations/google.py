"""Google Generative AI integration — patches generate_content (sync + async)."""

from __future__ import annotations

import functools
import logging
import time
import uuid
from typing import Any

from capsule.core.context import get_current_session
from capsule.core.models import (
    EventType,
    LLMCallPayload,
    LLMMessage,
    LLMParameters,
    LLMResponse,
    LLMUsage,
)

logger = logging.getLogger("capsule.integrations.google")

_PATCHED = False


def patch() -> None:
    global _PATCHED
    if _PATCHED:
        return

    try:
        import google.generativeai as genai  # type: ignore[import-untyped]
    except ImportError:
        return

    _patch_generate_content(genai)
    _PATCHED = True
    logger.debug("capsule: Google Generative AI SDK patched")


def _patch_generate_content(genai: Any) -> None:
    original = genai.GenerativeModel.generate_content

    @functools.wraps(original)
    def patched(self: Any, contents: Any, **kwargs: Any) -> Any:
        session = get_current_session()
        if session is None:
            return original(self, contents, **kwargs)

        payload = LLMCallPayload(
            provider="google",
            model=getattr(self, "model_name", "gemini"),
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
                payload.cassette_ref = f"cassettes/{cassette_id}.json"
            except Exception:
                pass
            _emit_event(session, payload, duration)
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            payload.error = str(exc)
            _emit_event(session, payload, duration)
            raise

    genai.GenerativeModel.generate_content = patched


def _emit_event(session: Any, payload: LLMCallPayload, duration_ms: float) -> None:
    from capsule.core.models import Event

    event = Event(
        session_id=session.session_id,
        step_index=session.next_step_index(),
        event_type=EventType.LLM_CALL,
        duration_ms=duration_ms,
        payload=payload,
    )
    session.capture_event(event)
