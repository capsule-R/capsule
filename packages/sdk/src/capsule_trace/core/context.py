"""ContextVar-based session tracking — async-safe across concurrent agent calls."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from capsule_trace.core.session import Session

_current_session: ContextVar["Session | None"] = ContextVar(
    "capsule_session", default=None
)


def get_current_session() -> "Session | None":
    return _current_session.get()


def set_current_session(session: "Session | None") -> None:
    _current_session.set(session)
