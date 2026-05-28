"""ContextVar that activates cassette replay mode.

When replay mode is active, integration patches consult the CassetteStore
instead of making live API calls. Zero overhead when inactive.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from capsule.replay.cassette import CassetteStore

_replay_store: ContextVar["CassetteStore | None"] = ContextVar(
    "capsule_replay_store", default=None
)


def get_replay_store() -> "CassetteStore | None":
    return _replay_store.get()


def set_replay_store(store: "CassetteStore | None") -> None:
    _replay_store.set(store)


def is_replaying() -> bool:
    return _replay_store.get() is not None
