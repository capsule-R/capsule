"""ContextVar that activates cassette replay mode.

When replay mode is active, integration patches consult the CassetteStore
instead of making live API calls. Zero overhead when inactive.
"""

from __future__ import annotations

import contextlib
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from capsule_trace.replay.cassette import CassetteStore

_replay_store: ContextVar[CassetteStore | None] = ContextVar("capsule_replay_store", default=None)


def get_replay_store() -> CassetteStore | None:
    return _replay_store.get()


def set_replay_store(store: CassetteStore | None) -> None:
    _replay_store.set(store)


def is_replaying() -> bool:
    return _replay_store.get() is not None


@contextlib.contextmanager
def replay_scope(store: CassetteStore | None) -> Iterator[None]:
    """Activate `store` as the current replay store for the duration of the
    block, so patched integrations (openai.py, anthropic.py, google.py)
    consult get_replay_store() and serve from cassettes instead of hitting
    live APIs — then clear it again on exit.

    Without this, set_replay_store() had zero callers: replaying an archive
    never actually activated replay mode for any code re-executed during it.
    """
    set_replay_store(store)
    try:
        yield
    finally:
        set_replay_store(None)
