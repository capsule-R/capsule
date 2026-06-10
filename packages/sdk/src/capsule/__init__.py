"""Capsule — Deterministic replay & time-travel debugger for AI agents."""

from __future__ import annotations

from pathlib import Path

from capsule.core.decorator import trace
from capsule.core.session import Session, get_current_session

__version__ = "0.1.0"
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
