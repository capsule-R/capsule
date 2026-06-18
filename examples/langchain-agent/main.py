"""
Capsule SDK — LangChain Agent Example
======================================
What this does: runs a billing agent that looks up a customer balance and
processes a refund, capturing the LangChain LLM call via CapsuleCallbackHandler
and the tool calls via @capture_tool_call — all recorded into one .capsule
session. Runs in "demo mode" (no live LLM call) if OPENAI_API_KEY is not set,
so it works with no API key.

Requirements:
    pip install "capsule-trace[langchain]" langchain-openai

Run:
    OPENAI_API_KEY=sk-... python examples/langchain-agent/main.py
    # or, without a key, it runs in demo mode:
    python examples/langchain-agent/main.py
"""

from __future__ import annotations

import capsule_trace as capsule
from capsule_trace.integrations.langchain import CapsuleCallbackHandler
from capsule_trace.integrations.tools import capture_tool_call


# ── Define tools ──────────────────────────────────────────────

@capture_tool_call(tool_name="get_customer_balance", tool_namespace="billing")
def get_customer_balance(customer_id: str) -> dict:
    """Look up a customer's account balance."""
    # In production this would call your DB / API
    balances = {
        "cust_001": {"balance": 1500.0, "currency": "INR"},
        "cust_002": {"balance": 250.0, "currency": "INR"},
    }
    return balances.get(customer_id, {"error": "customer not found"})


@capture_tool_call(tool_name="process_refund", tool_namespace="billing")
def process_refund(customer_id: str, amount: float) -> dict:
    """Process a refund for a customer."""
    if amount > 1000:
        raise ValueError(f"Refund amount {amount} exceeds policy limit of 1000")
    return {"status": "refunded", "amount": amount, "customer_id": customer_id}


# ── Agent ─────────────────────────────────────────────────────

@capsule.trace(
    agent_name="billing-agent",
    tags=["billing", "refund", "langchain"],
)
def run_billing_agent(customer_id: str, refund_amount: float) -> str:
    """A billing agent that processes refunds using LangChain."""
    import os

    if not os.getenv("OPENAI_API_KEY"):
        # Demo mode — simulate the agent without a live API call
        return _demo_run(customer_id, refund_amount)

    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage

    handler = CapsuleCallbackHandler()
    llm = ChatOpenAI(model="gpt-4o-mini", callbacks=[handler])

    # Step 1: Get balance
    balance_info = get_customer_balance(customer_id)

    # Step 2: Ask LLM whether to proceed
    prompt = (
        f"Customer {customer_id} has balance {balance_info}. "
        f"They are requesting a refund of {refund_amount} INR. "
        f"Should I proceed? Reply YES or NO and briefly explain."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    decision = response.content

    # Step 3: Process if approved
    if "YES" in decision.upper():
        result = process_refund(customer_id, refund_amount)
        return f"Refund processed: {result}"

    return f"Refund denied: {decision}"


def _demo_run(customer_id: str, refund_amount: float) -> str:
    """Simulate the agent flow without a real API key."""
    from capsule_trace.core.context import get_current_session
    from capsule_trace.core.models import (
        Event,
        EventType,
        LLMCallPayload,
        LLMMessage,
        LLMResponse,
        LLMUsage,
    )

    # Tool calls are already captured by @capture_tool_call decorators
    balance = get_customer_balance(customer_id)

    # Simulate an LLM decision event
    session = get_current_session()
    if session:
        payload = LLMCallPayload(
            provider="openai",
            model="gpt-4o-mini",
            messages=[LLMMessage(role="user", content=f"Process refund for {customer_id}?")],
            response=LLMResponse(
                content=f"YES — balance {balance['balance']} INR is sufficient for refund of {refund_amount} INR.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=45, completion_tokens=20, total_tokens=65),
            ),
        )
        event = Event(
            session_id=session.session_id,
            step_index=session.next_step_index(),
            event_type=EventType.LLM_CALL,
            duration_ms=280.0,
            payload=payload,
        )
        session.capture_event(event)

    result = process_refund(customer_id, refund_amount)
    return f"Refund processed: {result}"


def main() -> None:
    from capsule_trace.storage.sqlite import SQLiteBackend

    print("Running billing agent (demo mode)...\n")
    output = run_billing_agent("cust_001", 500.0)
    print(f"Result: {output}\n")

    backend = SQLiteBackend.default()
    sessions = backend.list_sessions(limit=1)
    if sessions:
        s = sessions[0]
        events = backend.read_events(s.session_id)
        print(f"Session captured: {s.session_id}")
        print(f"  Events: {len(events)}")
        for e in events:
            name = ""
            if isinstance(e.payload, dict):
                name = e.payload.get("tool_name") or e.payload.get("model") or ""
            print(f"    [{e.step_index}] {e.event_type.value} — {name}")
        print(f"\n  capsule replay {s.session_id}")


if __name__ == "__main__":
    main()
