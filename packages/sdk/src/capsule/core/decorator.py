"""@capsule.trace decorator — wraps a function or coroutine in a Session."""

from __future__ import annotations

import asyncio
import functools
import os
from typing import Any, Callable, TypeVar

from capsule.core.session import Session

F = TypeVar("F", bound=Callable[..., Any])

_DISABLED_ENV = "CAPSULE_DISABLE"


def _is_disabled() -> bool:
    return os.environ.get(_DISABLED_ENV, "").strip().lower() in ("1", "true", "yes")


def trace(
    agent_name: str | None = None,
    agent_version: str | None = None,
    tags: list[str] | None = None,
    user_metadata: dict[str, Any] | None = None,
    redact: list[str] | None = None,
    auto_upload: bool = False,
    storage_backend: Any | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function in a Capsule session.

    Usage::

        @capsule.trace(agent_name="billing-agent")
        def run_agent(customer_id: str) -> str:
            ...

        @capsule.trace(agent_name="async-agent")
        async def run_async_agent(query: str) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        name = agent_name or fn.__name__

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if _is_disabled():
                    return await fn(*args, **kwargs)

                session = Session(
                    agent_name=name,
                    agent_version=agent_version,
                    tags=tags,
                    user_metadata=user_metadata,
                    redact=redact,
                    auto_upload=auto_upload,
                    storage_backend=storage_backend,
                )
                async with session:
                    return await fn(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        else:

            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if _is_disabled():
                    return fn(*args, **kwargs)

                session = Session(
                    agent_name=name,
                    agent_version=agent_version,
                    tags=tags,
                    user_metadata=user_metadata,
                    redact=redact,
                    auto_upload=auto_upload,
                    storage_backend=storage_backend,
                )
                with session:
                    return fn(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator
