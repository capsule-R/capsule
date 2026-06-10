"""capsule_sdk — public entry point for the Capsule SDK.

Users import this package as ``import capsule_sdk as capsule``.  All symbols
live in the ``capsule`` namespace; this module re-exports them so that the
pip-installable name (``capsule-sdk``) matches the Python import name.
"""

from capsule import (  # noqa: F401
    Session,
    __version__,
    get_current_session,
    last_session_path,
    trace,
)

__all__ = ["trace", "Session", "get_current_session", "last_session_path", "__version__"]
