"""Capsule — Deterministic replay & time-travel debugger for AI agents."""

from capsule.core.decorator import trace
from capsule.core.session import Session, get_current_session

__version__ = "0.1.0"
__all__ = ["trace", "Session", "get_current_session"]
