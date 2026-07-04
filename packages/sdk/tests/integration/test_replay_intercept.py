"""P1: Anthropic and Google must short-circuit to cassettes during replay,
exactly like the OpenAI integration already does. Before this fix, only
OpenAI checked get_replay_store() — Anthropic/Google calls during "replay"
hit the live API with real keys, costing money and breaking determinism.

Each test uses a deliberately invalid API key; if the integration failed to
short-circuit and made a real network call, it would raise an auth/network
error rather than returning the cassette response.
"""

from __future__ import annotations

import pytest

from capsule_trace.replay.cassette import CassetteMissError, CassetteStore, compute_request_hash
from capsule_trace.replay.mode import set_replay_store


@pytest.fixture(autouse=True)
def _clear_replay_store():
    yield
    set_replay_store(None)


def test_anthropic_serves_from_cassette_during_replay_no_live_call():
    import anthropic as anthropic_sdk

    from capsule_trace.integrations import anthropic as capsule_anthropic

    capsule_anthropic.patch()

    messages = [{"role": "user", "content": "hello"}]
    store = CassetteStore(
        {
            "llm-a": {
                "request_hash": compute_request_hash(
                    model="claude-3-opus", messages=messages, max_tokens=100
                ),
                "raw_response": {
                    "content": [{"type": "text", "text": "cassette answer"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 3, "output_tokens": 2},
                },
            }
        }
    )
    set_replay_store(store)

    # Deliberately invalid key — a real network call here would raise, not
    # return successfully.
    client = anthropic_sdk.Anthropic(api_key="sk-ant-invalid-test-key")
    response = client.messages.create(model="claude-3-opus", max_tokens=100, messages=messages)

    assert response.content[0].text == "cassette answer"
    assert response.content[0].type == "text"


def test_anthropic_raises_cassette_miss_for_unmatched_request():
    import anthropic as anthropic_sdk

    from capsule_trace.integrations import anthropic as capsule_anthropic

    capsule_anthropic.patch()

    store = CassetteStore({})  # no cassettes at all
    set_replay_store(store)

    client = anthropic_sdk.Anthropic(api_key="sk-ant-invalid-test-key")
    with pytest.raises(CassetteMissError):
        client.messages.create(
            model="claude-3-opus",
            max_tokens=100,
            messages=[{"role": "user", "content": "never recorded"}],
        )


def test_google_serves_from_cassette_during_replay_no_live_call():
    import google.generativeai as genai

    from capsule_trace.integrations import google as capsule_google

    capsule_google.patch()

    store = CassetteStore(
        {
            "llm-a": {
                # GenerativeModel("gemini-pro").model_name comes back
                # SDK-normalized as "models/gemini-pro".
                "request_hash": compute_request_hash(
                    model="models/gemini-pro",
                    messages=[{"role": "user", "content": "hello gemini"}],
                ),
                "raw_response": {
                    "text": "cassette gemini answer",
                    "candidates": [{"finish_reason": "STOP"}],
                },
            }
        }
    )
    set_replay_store(store)

    genai.configure(api_key="invalid-test-key")
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content("hello gemini")

    assert response.text == "cassette gemini answer"


def test_google_raises_cassette_miss_for_unmatched_request():
    import google.generativeai as genai

    from capsule_trace.integrations import google as capsule_google

    capsule_google.patch()

    store = CassetteStore({})
    set_replay_store(store)

    genai.configure(api_key="invalid-test-key")
    model = genai.GenerativeModel("gemini-pro")
    with pytest.raises(CassetteMissError):
        model.generate_content("never recorded")
