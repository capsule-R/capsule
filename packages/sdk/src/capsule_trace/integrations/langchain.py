"""LangChain callback handler — integrates Capsule capture into any LangChain chain or agent.

Usage::

    from langchain_openai import ChatOpenAI
    from capsule_trace.integrations.langchain import CapsuleCallbackHandler
    import capsule_trace

    @capsule.trace(agent_name="langchain-agent")
    def run():
        llm = ChatOpenAI(callbacks=[CapsuleCallbackHandler()])
        return llm.invoke("Hello!")
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Union
from uuid import UUID

from capsule_trace.core.context import get_current_session
from capsule_trace.core.models import (
    Event,
    EventType,
    LLMCallPayload,
    LLMMessage,
    LLMParameters,
    LLMResponse,
    LLMUsage,
    ToolCallPayload,
)

logger = logging.getLogger("capsule.integrations.langchain")

try:
    from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore[import-untyped]
    from langchain_core.messages import BaseMessage  # type: ignore[import-untyped]
    from langchain_core.outputs import LLMResult  # type: ignore[import-untyped]

    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object  # type: ignore[assignment,misc]


class CapsuleCallbackHandler(BaseCallbackHandler):  # type: ignore[misc]
    """LangChain callback handler that records LLM calls and tool invocations
    into the current Capsule session.

    Pass as a callback to any LangChain LLM, chain, or agent::

        llm = ChatOpenAI(callbacks=[CapsuleCallbackHandler()])
    """

    def __init__(self) -> None:
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain-core is required. Install with: pip install capsule-trace[langchain]"
            )
        super().__init__()
        self._call_start_times: dict[UUID, float] = {}

    # ── LLM events ───────────────────────────────────────────

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._call_start_times[run_id] = time.perf_counter()

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._call_start_times[run_id] = time.perf_counter()

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        session = get_current_session()
        if session is None:
            return

        start = self._call_start_times.pop(run_id, time.perf_counter())
        duration = (time.perf_counter() - start) * 1000

        try:
            # Extract model info from response metadata if available
            model_name = "unknown"
            if hasattr(response, "llm_output") and response.llm_output:
                model_name = response.llm_output.get("model_name", "unknown")

            generations = response.generations or [[]]
            flat = [g for gen_list in generations for g in gen_list]
            content = flat[0].text if flat else None

            token_usage: dict[str, int] = {}
            if hasattr(response, "llm_output") and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})

            cassette_id = f"llm-{uuid.uuid4().hex[:8]}"
            payload = LLMCallPayload(
                provider="langchain",
                model=model_name,
                messages=[],
                response=LLMResponse(
                    content=content,
                    usage=LLMUsage(
                        prompt_tokens=token_usage.get("prompt_tokens", 0),
                        completion_tokens=token_usage.get("completion_tokens", 0),
                        total_tokens=token_usage.get("total_tokens", 0),
                    ),
                ),
                cassette_ref=f"cassettes/{cassette_id}.json",
            )
            event = Event(
                session_id=session.session_id,
                step_index=session.next_step_index(),
                event_type=EventType.LLM_CALL,
                duration_ms=duration,
                payload=payload,
            )
            session.capture_event(event)
        except Exception:
            logger.debug("capsule: LangChain on_llm_end failed", exc_info=True)

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._call_start_times.pop(run_id, None)

    # ── Tool events ──────────────────────────────────────────

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._call_start_times[run_id] = time.perf_counter()

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        session = get_current_session()
        if session is None:
            return

        start = self._call_start_times.pop(run_id, time.perf_counter())
        duration = (time.perf_counter() - start) * 1000

        try:
            cassette_id = f"tool-{uuid.uuid4().hex[:8]}"
            payload = ToolCallPayload(
                tool_name=kwargs.get("name", "unknown_tool"),
                arguments={"input": kwargs.get("input", "")},
                result=output,
                execution_duration_ms=duration,
                cassette_ref=f"cassettes/{cassette_id}.json",
            )
            event = Event(
                session_id=session.session_id,
                step_index=session.next_step_index(),
                event_type=EventType.TOOL_CALL,
                duration_ms=duration,
                payload=payload,
            )
            session.capture_event(event)
        except Exception:
            logger.debug("capsule: LangChain on_tool_end failed", exc_info=True)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._call_start_times.pop(run_id, None)
