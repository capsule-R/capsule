# capsule-sdk

**Deterministic replay & time-travel debugger for AI agents.**

```bash
pip install capsule-sdk
```

---

## Quick Start

```python
import capsule_sdk as capsule

@capsule.trace(agent_name="my-agent")
def run_agent(query: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}],
    )
    return response.choices[0].message.content
```

That's it. Every LLM call is now captured automatically.

## CLI

```bash
# List captured sessions
capsule-sdk list

# Inspect a session step by step
capsule-sdk show ses_01HXYZ123

# Export to shareable file
capsule-sdk export ses_01HXYZ123 --output bug.capsule

# Replay deterministically
capsule-sdk replay ses_01HXYZ123

# Branch from step 7 with different temperature
capsule-sdk branch ses_01HXYZ123 --from-step 7 --modify temperature=0.0

# Diff two sessions
capsule-sdk diff ses_01HXYZ ses_01HABC
```

## Supported Providers

| Provider | Status |
|----------|--------|
| OpenAI (sync + async) | ✅ Sprint 2 |
| Anthropic (sync + async) | ✅ Sprint 2 |
| Google Generative AI | ✅ Sprint 2 |
| LangChain | Sprint 4 |
| LangGraph | Sprint 4 |

## Disable at Runtime

```bash
CAPSULE_DISABLE=1 python my_agent.py
```

Zero overhead when disabled — checked once at function entry.

## License

Apache 2.0 — see [LICENSE](LICENSE).
