"""Capsule — Deterministic replay & time-travel debugger for AI agents."""

from __future__ import annotations

from pathlib import Path

from capsule_trace.core.decorator import trace
from capsule_trace.core.session import Session, get_current_session

# Auto-activate integrations for every provider SDK that is installed
# (OpenAI, Anthropic, Google Generative AI). autopatch_all() is the single
# entry point — it import-guards each provider and patches it if present, so
# importing capsule_trace instruments all of them without manual setup.
from capsule_trace.integrations.autopatch import autopatch_all

autopatch_all()

__version__ = "0.1.2"
__all__ = ["trace", "Session", "get_current_session", "last_session_path"]


def last_session_path() -> Path | None:
    """Return the path of the most recently saved .capsule file, or None."""
    candidates: list[Path] = []
    for search_dir in (Path.home() / ".capsule", Path.cwd()):
        if search_dir.is_dir():
            candidates.extend(search_dir.glob("*.capsule"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)
