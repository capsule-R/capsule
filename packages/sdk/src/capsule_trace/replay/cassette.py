"""CassetteStore — maps cassette refs to stored API responses."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Any


class CassetteMissError(RuntimeError):
    """Raised when replay needs a cassette that isn't in the store.

    Previously a missing cassette was either silently skipped or served the
    next unrelated one in insertion order — both hide a real divergence
    between the recorded session and what's being replayed. Failing loudly
    here is the correct behavior for a determinism-checking tool.
    """


def compute_request_hash(
    model: str,
    messages: Any,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Canonical hash of the parts of an LLM request that determine its
    response, used to match a live call to the cassette recorded for it —
    independent of tar/insertion order, which is not the same as recording
    order and previously caused wrong cassettes to be served silently.

    `sort_keys=True` normalizes key order within messages/params so the same
    logical request always hashes the same way regardless of how the caller
    built the dict.
    """
    canonical = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    blob = json.dumps(canonical, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


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
        # Index by the cassette's own recorded request_hash (see
        # compute_request_hash) — this is what get_by_request_hash uses, and
        # is independent of tar/insertion order.
        self._by_request_hash: dict[str, Any] = {}
        for cassette_data in self._data.values():
            if isinstance(cassette_data, dict):
                request_hash = cassette_data.get("request_hash")
                if request_hash:
                    self._by_request_hash[request_hash] = cassette_data

    def get(self, cassette_ref: str) -> Any | None:
        """Lookup by full ref path OR bare ID."""
        bare = cassette_ref.removeprefix("cassettes/").removesuffix(".json")
        return self._data.get(bare)

    def get_by_request_hash(self, request_hash: str) -> Any | None:
        """Lookup by the canonical request hash recorded at capture time —
        the correct way to match a live call to its cassette, regardless of
        which order cassettes happen to appear in the archive."""
        return self._by_request_hash.get(request_hash)

    def _pop_next(self) -> Any | None:
        """Return and remove the next cassette in insertion order.

        Retained for cassette types that don't carry a request_hash (e.g.
        tool calls); LLM call replay should prefer get_by_request_hash.
        """
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
