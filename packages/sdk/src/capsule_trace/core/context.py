"""ContextVar-based session tracking — async-safe across concurrent agent calls."""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from capsule_trace.core.session import Session

_current_session: contextvars.ContextVar[Session | None] = contextvars.ContextVar(
    "capsule_session", default=None
)


def get_current_session() -> Session | None:
    return _current_session.get()


def set_current_session(session: Session | None) -> None:
    _current_session.set(session)


def copy_context_for_thread() -> contextvars.Context:
    """Snapshot the current context (including the active Capsule session)
    for use inside a thread you spawn yourself.

    asyncio tasks inherit a copy of the calling context automatically;
    threading.Thread and ThreadPoolExecutor do not — a thread started this
    way sees get_current_session() as None, so nothing it does gets
    captured, silently. Run your thread's target through the returned
    context: ``ctx = copy_context_for_thread(); thread = Thread(target=ctx.run, args=(fn, ...))``.
    Prefer wrap_executor() for ThreadPoolExecutor.
    """
    return contextvars.copy_context()


def wrap_executor(executor: Executor) -> Executor:
    """Wrap an Executor so every submitted task runs with the *submitting*
    thread's context (including the active Capsule session) propagated.

    The most common agent pattern — parallel tool calls via
    ThreadPoolExecutor — silently records zero events without this, because
    spawned threads don't inherit ContextVars by default. Usage::

        with Session(agent_name="my-agent") as s:
            with s.wrap_executor(ThreadPoolExecutor(max_workers=4)) as pool:
                futures = [pool.submit(call_tool, arg) for arg in args]
    """
    original_submit = executor.submit

    def _submit(fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        ctx = contextvars.copy_context()
        return original_submit(ctx.run, fn, *args, **kwargs)

    executor.submit = _submit  # type: ignore[method-assign]
    return executor
