"""LangGraph integration — hooks into StateGraph to capture node executions.

Usage::

    from langgraph.graph import StateGraph
    from capsule_trace.integrations.langgraph import add_capsule_tracing
    import capsule_trace

    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", execute_tools)
    add_capsule_tracing(graph)          # <-- one line

    @capsule.trace(agent_name="langgraph-agent")
    def run():
        app = graph.compile()
        return app.invoke({"messages": [...]})
"""

from __future__ import annotations

import contextlib
import logging
import time
from typing import Any

from capsule_trace.core.context import get_current_session
from capsule_trace.core.models import Event, EventType, ToolCallPayload

logger = logging.getLogger("capsule.integrations.langgraph")


def add_capsule_tracing(graph: Any) -> Any:
    """Wrap all nodes in a LangGraph StateGraph with Capsule capture.

    Returns the graph (mutated in place) for chaining::

        graph = add_capsule_tracing(StateGraph(State))
    """
    try:
        # LangGraph stores nodes in _nodes dict
        nodes = getattr(graph, "_nodes", {})
        for node_name, node_spec in list(nodes.items()):
            original_fn = (
                node_spec.get("runnable")
                if isinstance(node_spec, dict)
                else getattr(node_spec, "runnable", None)
            )
            if original_fn is None:
                continue
            nodes[node_name] = _wrap_node(node_name, original_fn, node_spec)
    except Exception:
        logger.debug("capsule: failed to instrument LangGraph nodes", exc_info=True)

    return graph


def _wrap_node(name: str, fn: Any, spec: Any) -> Any:
    """Return a new node spec with the function wrapped for capture."""
    import functools

    @functools.wraps(fn)
    def wrapped(state: Any, *args: Any, **kwargs: Any) -> Any:
        session = get_current_session()
        start = time.perf_counter()
        result = None
        error = None
        try:
            result = fn(state, *args, **kwargs)
            return result  # noqa: RET504
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if session is not None:
                duration = (time.perf_counter() - start) * 1000
                _emit_node_event(session, name, state, result, error, duration)

    if isinstance(spec, dict):
        new_spec = dict(spec)
        new_spec["runnable"] = wrapped
        return new_spec

    # If spec is an object, try to replace the runnable attribute
    with contextlib.suppress(AttributeError):
        spec.runnable = wrapped
    return spec


def _emit_node_event(
    session: Any,
    node_name: str,
    state: Any,
    result: Any,
    error: str | None,
    duration_ms: float,
) -> None:
    try:
        import json

        def safe_repr(obj: Any) -> Any:
            try:
                return json.loads(json.dumps(obj, default=str))
            except Exception:
                return str(obj)

        payload = ToolCallPayload(
            tool_name=node_name,
            tool_namespace="langgraph.node",
            arguments=safe_repr(state) if isinstance(state, dict) else {"state": str(state)},
            result=safe_repr(result),
            error=error,
            execution_duration_ms=duration_ms,
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
        logger.debug("capsule: failed to emit LangGraph node event", exc_info=True)
