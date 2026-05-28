"""
Capsule SDK — OpenAI Basic Example
===================================
Demonstrates capturing an OpenAI agent with one decorator,
then listing and exporting the captured session.

Requirements:
    pip install capsule-sdk openai

Run:
    OPENAI_API_KEY=sk-... python examples/openai-basic/main.py
"""

from __future__ import annotations

import os
from pathlib import Path

import capsule
from capsule.storage.sqlite import SQLiteBackend

# ── Auto-patch OpenAI at import time ──────────────────────────
from capsule.integrations.autopatch import autopatch_all

autopatch_all()

from openai import OpenAI  # noqa: E402  — must come after autopatch


@capsule.trace(
    agent_name="openai-basic-agent",
    tags=["example", "openai"],
)
def run_agent(user_query: str) -> str:
    """A simple single-turn agent that answers a question."""
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": user_query},
        ],
        temperature=0.7,
        max_tokens=256,
    )

    return response.choices[0].message.content or ""


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to run against the live API.")
        print("Running in demo mode with a mock response...\n")

        # Demo mode — simulate a captured session without a real API key
        _run_demo()
        return

    print("Running agent...")
    answer = run_agent("What is the capital of France, and why is it famous?")
    print(f"\nAgent answer: {answer}\n")

    # Show what was captured
    backend = SQLiteBackend.default()
    sessions = backend.list_sessions(limit=1)
    if sessions:
        s = sessions[0]
        print(f"Captured session: {s.session_id}")
        print(f"  Agent:    {s.agent_name}")
        print(f"  Status:   {s.status.value}")
        print(f"  Steps:    {s.step_count}")
        print(f"  Duration: {s.duration_ms:.0f}ms\n")

        # Export to .capsule file
        from capsule.core.exporter import export_capsule

        out = Path("example-session.capsule")
        export_capsule(s.session_id, backend, out)
        size_kb = out.stat().st_size / 1024
        print(f"Exported to {out} ({size_kb:.1f} KB)")
        print("\nTo replay:")
        print(f"  capsule replay {s.session_id}")
        print(f"  capsule export {s.session_id} --output example-session.capsule")


def _run_demo() -> None:
    """Simulate a capture without a real API key to show the data model."""
    import capsule
    from capsule.core.models import Event, EventType, LLMCallPayload, LLMMessage, LLMResponse, LLMUsage
    from capsule.core.session import Session

    storage = SQLiteBackend.default()

    with Session(
        agent_name="openai-basic-agent",
        tags=["example", "openai", "demo"],
        storage_backend=storage,
    ) as s:
        # Simulate an LLM call event
        payload = LLMCallPayload(
            provider="openai",
            model="gpt-4o-mini",
            messages=[
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="What is the capital of France?"),
            ],
            response=LLMResponse(
                content="Paris is the capital of France. It is famous for the Eiffel Tower, the Louvre museum, and its rich history as a center of art, culture, and cuisine.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=28, completion_tokens=36, total_tokens=64),
            ),
        )
        event = Event(
            session_id=s.session_id,
            step_index=s.next_step_index(),
            event_type=EventType.LLM_CALL,
            duration_ms=342.0,
            payload=payload,
        )
        s.capture_event(event)

    sessions = storage.list_sessions(limit=1)
    if sessions:
        meta = sessions[0]
        print(f"Demo session captured: {meta.session_id}")
        print(f"  Agent:  {meta.agent_name}")
        print(f"  Status: {meta.status.value}")
        print(f"  Steps:  {meta.step_count}")
        print()
        print("Try these commands:")
        print(f"  capsule list")
        print(f"  capsule show {meta.session_id}")
        print(f"  capsule export {meta.session_id} --output demo.capsule")


if __name__ == "__main__":
    main()
