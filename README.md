# Capsule

**Deterministic Replay & Time-Travel Debugger for AI Agents**

[![CI](https://github.com/capsule-dev/capsule/actions/workflows/ci.yml/badge.svg)](https://github.com/capsule-dev/capsule/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/capsule-sdk)](https://pypi.org/project/capsule-sdk/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

When an AI agent fails in production — deletes wrong data, sends wrong email, charges wrong amount — engineers today have no way to replay the exact failure. LLM outputs are non-deterministic. There's no stack trace. No `pdb`. No crash dump.

**Capsule fixes this.**

It captures every LLM call, tool invocation, and memory operation into a portable `.capsule` file you can replay offline, branch from any step, and attach to any bug report — exactly the way you attach screenshots today.

---

## Quick Start

```bash
pip install capsule-sdk
```

```python
import capsule
from openai import OpenAI

@capsule.trace(agent_name="billing-agent")
def run_agent(customer_id: str):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Process refund for {customer_id}"}],
    )
    return response.choices[0].message.content

run_agent("cust_001")
```

```bash
# List captured sessions
capsule list

# Replay the last failure
capsule replay ses_01HXYZ123456

# Branch from step 7 with a different temperature
capsule branch ses_01HXYZ123456 --from-step 7 --modify temperature=0.0

# Export to a shareable file
capsule export ses_01HXYZ123456 --output bug-report.capsule
```

---

## Why Capsule?

| Feature | LangSmith | Langfuse | AgentOps | **Capsule** |
|---------|-----------|----------|----------|-------------|
| Tracing / observability | ✅ | ✅ | ✅ | ✅ |
| Deterministic replay | ❌ | ❌ | ❌ | ✅ |
| Branch from any step | ❌ | ❌ | ❌ | ✅ |
| Portable file format | ❌ | ❌ | ❌ | ✅ |
| Works fully offline | ❌ | ❌ | ❌ | ✅ |
| Framework agnostic | ❌ | ✅ | ✅ | ✅ |

---

## Repository Structure

```
capsule/
├── packages/
│   ├── sdk/                  # Python SDK (Apache 2.0, open source)
│   ├── replay-engine/        # Rust replay engine (Apache 2.0)
│   ├── cloud-api/            # FastAPI cloud backend (proprietary)
│   ├── cloud-web/            # Next.js web dashboard (proprietary)
│   └── vscode-extension/     # VS Code extension
├── docs/
│   └── spec/                 # .capsule format specification
├── examples/                 # Working code examples
└── infra/                    # Terraform infrastructure
```

---

## Documentation

- [Quick Start Guide](docs/guides/quickstart.md)
- [.capsule Format Specification](docs/spec/capsule-format-v1.md)
- [API Reference](docs/api/)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

## Three-Layer Product

| Layer | License | Pricing |
|-------|---------|---------|
| Python SDK + CLI | Apache 2.0 | Free forever |
| Cloud Platform | Proprietary | $49–$599/month |
| Enterprise (self-hosted) | Commercial | Custom |

---

## Contributing

We welcome contributions to the open-source SDK and replay engine. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## License

The SDK (`packages/sdk/`) and replay engine (`packages/replay-engine/`) are licensed under the [Apache 2.0 License](LICENSE).

The cloud platform (`packages/cloud-api/`, `packages/cloud-web/`) is proprietary software. All rights reserved.
