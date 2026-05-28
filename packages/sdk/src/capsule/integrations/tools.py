"""Tool / function-call capture helpers.

Provides `capture_tool_call` — a decorator and context manager that wraps
any Python function and records its invocation as a ToolCall event in the
current Capsule session.

Works with:
- OpenAI function calling (wrap the function the model calls)
- Anthropic tool use (wrap the function matching tool_name)
- Manual wrapping for any arbitrary tool
"""

from __future__ import annotations

import functools
import logging
import time
import traceback
import uuid
from typing import Any, Callable, TypeVar

from capsule.core.context import get_current_session
from capsule.core.models import Event, EventType, ToolCallPayload

logger = logging.getLogger("capsule.integrations.tools")

F = TypeVar("F", bound=Callable[..., Any])


def capture_tool_call(
    tool_name: str | None = None,
    tool_namespace: str | None = None,
    tool_version: str | None = None,
) -> Callable[[F], F]:
    """Decorator: wrap a Python function and capture it as a ToolCall event.

    Usage::

        @capture_tool_call(tool_name="get_balance", tool_namespace="billing")
        def get_balance(customer_id: str) -> dict:
            return {"balance": 1500.0, "currency": "INR"}
    """

    def decorator(fn: F) -> F:
        name = tool_name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = get_current_session()
            if session is None:
                return fn(*args, **kwargs)

            # Build argument dict from positional + keyword args
            import inspect
            try:
                sig = inspect.signature(fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arg_dict: dict[str, Any] = dict(bound.arguments)
            except Exception:
                arg_dict = {"args": list(args), **kwargs}

            start = time.perf_counter()
            result: Any = None
            error: str | None = None
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                duration = (time.perf_counter() - start) * 1000
                _emit_tool_event(
                    session=session,
                    name=name,
                    namespace=tool_namespace,
                    version=tool_version,
                    arguments=arg_dict,
                    result=result,
                    error=error,
                    duration_ms=duration,
                )

        return wrapper  # type: ignore[return-value]

    return decorator


def _emit_tool_event(
    session: Any,
    name: str,
    namespace: str | None,
    version: str | None,
    arguments: dict[str, Any],
    result: Any,
    error: str | None,
    duration_ms: float,
) -> None:
    try:
        cassette_id = f"tool-{uuid.uuid4().hex[:8]}"
        payload = ToolCallPayload(
            tool_name=name,
            tool_namespace=namespace,
            tool_version=version,
            arguments=arguments,
            result=result,
            error=error,
            execution_duration_ms=duration_ms,
            cassette_ref=f"cassettes/{cassette_id}.json",
        )
        event = Event(
            session_id=session.session_id,
            step_index=session.next_step_index(),
            event_type=EventType.TOOL_CALL,
            duration_ms=duration_ms,
            payload=payload,
        )
        session.capture_event(event)
    except Exception:
        logger.debug("capsule: failed to emit tool event", exc_info=True)


# ── OpenAI function-calling interception ─────────────────────

def intercept_openai_tool_calls(response: Any, session: Any) -> None:
    """After an OpenAI response with tool_calls, capture each as a ToolCall event.

    Call this immediately after `client.chat.completions.create()` if the
    response contains tool_calls.  The function calls themselves are captured
    separately when the tool functions execute.
    """
    try:
        for choice in response.choices or []:
            if not choice.message.tool_calls:
                continue
            for tc in choice.message.tool_calls:
                import json as _json

                args_str = tc.function.arguments or "{}"
                try:
                    args_dict = _json.loads(args_str)
                except Exception:
                    args_dict = {"_raw": args_str}

                cassette_id = f"tool-{uuid.uuid4().hex[:8]}"
                payload = ToolCallPayload(
                    tool_name=tc.function.name,
                    arguments=args_dict,
                    cassette_ref=f"cassettes/{cassette_id}.json",
                )
                event = Event(
                    session_id=session.session_id,
                    step_index=session.next_step_index(),
                    event_type=EventType.TOOL_CALL,
                    duration_ms=0.0,
                    payload=payload,
                )
                session.capture_event(event)
    except Exception:
        logger.debug("capsule: failed to capture OpenAI tool calls", exc_info=True)
