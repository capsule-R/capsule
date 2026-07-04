"""P0-2 regression test — cassettes must actually be persisted during capture.

Before this fix, every integration set ``payload.cassette_ref`` to a filename
that nothing ever wrote (see integrations/openai.py, anthropic.py, google.py,
tools.py, langchain.py). Exported ``.capsule`` archives contained zero
cassette files, so replay always failed with "no cassette available for
replay step" on any real recording. This test exercises the real patched
OpenAI client (not a hand-built Event/payload) end to end through export.
"""

from __future__ import annotations

import io
import json
import tarfile
from unittest.mock import MagicMock, patch

import pytest
import zstandard as zstd

from capsule_trace.core.exporter import export_capsule
from capsule_trace.core.session import Session
from capsule_trace.integrations import openai as capsule_openai
from capsule_trace.storage.sqlite import SQLiteBackend


@pytest.fixture()
def backend(tmp_path):
    return SQLiteBackend(tmp_path / "test.db")


def _mock_openai_response(content: str = "Mocked response") -> MagicMock:
    response = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    choice.message.tool_calls = None
    choice.finish_reason = "stop"
    response.choices = [choice]
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 5
    response.usage.total_tokens = 15
    response.model_dump.return_value = {
        "id": "chatcmpl-test",
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    return response


def test_cassette_written_during_capture_and_exported(tmp_path, backend):
    import openai as openai_sdk

    capsule_openai.patch()

    mock_response = _mock_openai_response()
    client = openai_sdk.OpenAI(api_key="test-key")

    # Patch the *instance* attribute — this is what the data-descriptor
    # design in openai.py is built to intercept (see its module docstring).
    with (
        patch.object(client.chat.completions, "create", MagicMock(return_value=mock_response)),
        Session(agent_name="cassette-test", storage_backend=backend) as s,
    ):
        session_id = s.session_id
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hello"}],
        )

    cassettes = backend.read_cassettes(session_id)
    assert len(cassettes) == 1, "expected the LLM call to persist exactly one cassette"

    cassette_data = next(iter(cassettes.values()))
    assert cassette_data["request"]["model"] == "gpt-4o"
    assert cassette_data["raw_response"]["choices"][0]["message"]["content"] == "Mocked response"

    # The archive must actually contain the cassette file the event's
    # cassette_ref points at — this is what replay reads from.
    output = tmp_path / "session.capsule"
    export_capsule(session_id, backend, output)

    dctx = zstd.ZstdDecompressor()
    tar_bytes = dctx.decompress(output.read_bytes())
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        cassette_names = [n for n in tar.getnames() if n.startswith("cassettes/")]
        assert len(cassette_names) == 1
        archived = json.loads(tar.extractfile(cassette_names[0]).read())

    assert archived["request"]["model"] == "gpt-4o"
    assert archived["raw_response"]["choices"][0]["message"]["content"] == "Mocked response"


def test_error_cassette_written_on_failed_call(tmp_path, backend):
    """A failed LLM call should also leave a cassette recording the failure,
    not just a dangling cassette_ref."""
    import openai as openai_sdk

    capsule_openai.patch()

    client = openai_sdk.OpenAI(api_key="test-key")

    with (
        patch.object(
            client.chat.completions,
            "create",
            MagicMock(side_effect=RuntimeError("rate limited")),
        ),
        pytest.raises(RuntimeError),
        Session(agent_name="cassette-error-test", storage_backend=backend) as s,
    ):
        session_id = s.session_id
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hello"}],
        )

    cassettes = backend.read_cassettes(session_id)
    assert len(cassettes) == 1
    cassette_data = next(iter(cassettes.values()))
    assert cassette_data["error"] == "rate limited"
    assert cassette_data["exception_type"] == "RuntimeError"
