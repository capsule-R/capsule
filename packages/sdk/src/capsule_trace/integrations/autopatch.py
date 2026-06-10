"""Auto-patch all installed provider SDKs at import time.

Called from capsule/__init__.py or the @trace decorator so users get
capture without any manual setup.
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger("capsule.integrations")


def autopatch_all() -> None:
    """Attempt to patch every supported provider SDK that is currently importable."""
    _try_patch("openai", "capsule.integrations.openai")
    _try_patch("anthropic", "capsule.integrations.anthropic")
    _try_patch("google.generativeai", "capsule.integrations.google")


def _try_patch(provider_module: str, capsule_module: str) -> None:
    try:
        importlib.import_module(provider_module)
    except ImportError:
        return

    try:
        mod = importlib.import_module(capsule_module)
        if hasattr(mod, "patch"):
            mod.patch()
    except Exception:
        logger.debug("capsule: failed to patch %s", provider_module, exc_info=True)
