"""CassetteStore — maps cassette refs to stored API responses."""

from __future__ import annotations

from collections import deque
from typing import Any


class CassetteStore:
    """Read-only map of cassette_ref → raw response data.

    Also supports sequential pop() for replay mode where the cassette
    position advances automatically with each intercepted call.
    """

    def __init__(self, cassettes: dict[str, Any]) -> None:
        # Key format: "cassettes/llm-xxxxxxxx.json"  OR  "llm-xxxxxxxx"
        self._data: dict[str, Any] = {}
        for k, v in cassettes.items():
            bare = k.removeprefix("cassettes/").removesuffix(".json")
            self._data[bare] = v
        # Sequential queue for replay mode (order of insertion = event order)
        self._queue: deque[Any] = deque(self._data.values())

    def get(self, cassette_ref: str) -> Any | None:
        """Lookup by full ref path OR bare ID."""
        bare = cassette_ref.removeprefix("cassettes/").removesuffix(".json")
        return self._data.get(bare)

    def _pop_next(self) -> Any | None:
        """Return and remove the next cassette in insertion order."""
        if self._queue:
            return self._queue.popleft()
        return None

    def reset(self) -> None:
        """Reset the sequential queue to the beginning (for re-replay)."""
        self._queue = deque(self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)
