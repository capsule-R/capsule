"""P1: autopatch_all() referenced the pre-rename "capsule.integrations.*"
package (the real one is "capsule_trace") — every patch attempt raised
ModuleNotFoundError, swallowed at DEBUG, so Google (only reachable via
autopatch — openai/anthropic are also patched directly at package import
time) was never actually instrumented."""

from __future__ import annotations

import logging

from capsule_trace.integrations import anthropic, autopatch, google, openai


def test_autopatch_all_patches_openai():
    autopatch.autopatch_all()
    assert openai._PATCHED is True
    assert isinstance(
        __import__("openai").resources.chat.completions.Completions.create,
        openai._CapsuleSyncDescriptor,
    )


def test_autopatch_all_patches_anthropic():
    autopatch.autopatch_all()
    assert anthropic._PATCHED is True


def test_autopatch_all_patches_google():
    """The specific regression: Google was never reachable via the old
    "capsule.integrations.google" path. Unlike openai/anthropic, nothing
    else patches Google at package-import time — this is the only path."""
    autopatch.autopatch_all()
    assert google._PATCHED is True

    import google.generativeai as genai

    # functools.wraps preserves __name__/__module__ from the original, so
    # identity (not name) is what distinguishes the patched callable.
    assert hasattr(genai.GenerativeModel.generate_content, "__wrapped__")


def test_autopatch_uses_correct_module_paths():
    """Regression guard for the exact bug: the module paths must point at
    capsule_trace, not the pre-rename "capsule" package."""
    import inspect

    source = inspect.getsource(autopatch.autopatch_all)
    assert "capsule_trace.integrations.openai" in source
    assert "capsule_trace.integrations.anthropic" in source
    assert "capsule_trace.integrations.google" in source
    assert "capsule.integrations" not in source.replace("capsule_trace.integrations", "")


def test_autopatch_logs_warning_not_debug_on_failure(monkeypatch, caplog):
    """A real patch failure must be visible by default (WARNING), not
    silently swallowed at DEBUG like the original bug."""
    original_import_module = autopatch.importlib.import_module

    def _fail_only_capsule_module(name, *args, **kwargs):
        if name.startswith("capsule_trace"):
            raise ModuleNotFoundError(f"No module named {name!r}")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(autopatch.importlib, "import_module", _fail_only_capsule_module)

    with caplog.at_level(logging.WARNING, logger="capsule.integrations"):
        # "openai" itself imports fine; only the internal capsule_trace
        # module import fails — this must hit the warning-logging branch,
        # not the silent "provider not installed" early return.
        autopatch._try_patch("openai", "capsule_trace.integrations.openai")

    assert any("failed to patch" in rec.message for rec in caplog.records)
