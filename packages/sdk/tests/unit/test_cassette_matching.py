"""P1: cassette serving must match the live call's own request hash — not
tar/insertion order, which is not the same as recording order and used to
serve the wrong cassette silently."""

from __future__ import annotations

import pytest

from capsule_trace.integrations.openai import _cassette_response_openai
from capsule_trace.replay.cassette import (
    CassetteMissError,
    CassetteStore,
    compute_request_hash,
)


def _cassette(model: str, messages: list[dict], content: str) -> dict:
    return {
        "request_hash": compute_request_hash(model=model, messages=messages),
        "request": {"model": model, "messages": messages},
        "raw_response": {
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    }


def test_compute_request_hash_is_deterministic_and_order_insensitive_for_keys():
    a = compute_request_hash(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
    b = compute_request_hash(model="gpt-4o", messages=[{"content": "hi", "role": "user"}])
    assert a == b  # key order within a message must not change the hash


def test_compute_request_hash_differs_for_different_requests():
    a = compute_request_hash(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
    b = compute_request_hash(model="gpt-4o", messages=[{"role": "user", "content": "bye"}])
    assert a != b


def test_replay_matches_cassette_by_request_hash_not_insertion_order():
    """Cassettes are inserted in an order that does NOT match how the live
    calls below will query them — correct matching must not depend on
    insertion/tar order."""
    messages_a = [{"role": "user", "content": "question A"}]
    messages_b = [{"role": "user", "content": "question B"}]

    store = CassetteStore(
        {
            # "b" recorded before "a" — the reverse of how they'll be queried.
            "llm-b": _cassette("gpt-4o", messages_b, "answer B"),
            "llm-a": _cassette("gpt-4o", messages_a, "answer A"),
        }
    )

    resp_a = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_a})
    resp_b = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_b})

    assert resp_a.choices[0].message.content == "answer A"
    assert resp_b.choices[0].message.content == "answer B"


def test_replay_raises_cassette_miss_error_for_unmatched_request():
    """A live call with no matching recorded request must fail loudly —
    silently serving an unrelated cassette (the old insertion-order
    behavior) hides a real divergence."""
    store = CassetteStore(
        {"llm-a": _cassette("gpt-4o", [{"role": "user", "content": "recorded question"}], "answer")}
    )

    with pytest.raises(CassetteMissError):
        _cassette_response_openai(
            store, {"model": "gpt-4o", "messages": [{"role": "user", "content": "never recorded"}]}
        )


def test_replay_matches_correctly_regardless_of_query_order():
    """Querying cassettes out of their recorded order must still resolve
    each one correctly — nothing should be consumed/popped by matching."""
    messages_a = [{"role": "user", "content": "A"}]
    messages_b = [{"role": "user", "content": "B"}]
    messages_c = [{"role": "user", "content": "C"}]

    store = CassetteStore(
        {
            "llm-a": _cassette("gpt-4o", messages_a, "resp-A"),
            "llm-b": _cassette("gpt-4o", messages_b, "resp-B"),
            "llm-c": _cassette("gpt-4o", messages_c, "resp-C"),
        }
    )

    # Query C, then A, then B — an order that matches neither insertion
    # order nor any sequential assumption.
    resp_c = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_c})
    resp_a = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_a})
    resp_b = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_b})

    assert resp_c.choices[0].message.content == "resp-C"
    assert resp_a.choices[0].message.content == "resp-A"
    assert resp_b.choices[0].message.content == "resp-B"

    # Querying A again must still resolve — matching doesn't consume entries.
    resp_a_again = _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages_a})
    assert resp_a_again.choices[0].message.content == "resp-A"


def test_replay_reproduces_recorded_error():
    """A request that was recorded as a failure should raise that failure
    on replay, not fabricate a successful response."""
    messages = [{"role": "user", "content": "will fail"}]
    store = CassetteStore(
        {
            "llm-err": {
                "request_hash": compute_request_hash(model="gpt-4o", messages=messages),
                "request": {"model": "gpt-4o", "messages": messages},
                "error": "rate limited",
                "exception_type": "RuntimeError",
            }
        }
    )

    with pytest.raises(RuntimeError, match="rate limited"):
        _cassette_response_openai(store, {"model": "gpt-4o", "messages": messages})
