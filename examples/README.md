# Capsule Examples

Runnable examples showing how to capture AI agent sessions with
[`capsule-trace`](https://pypi.org/project/capsule-trace/).

Every example has a built-in **demo mode**: if `OPENAI_API_KEY` is not set it
simulates the LLM call so you can see a `.capsule` session get captured without
spending tokens or needing a key.

## Setup

```bash
pip install capsule-trace
```

Some examples need extras (see each example's header). To run against the live
API, export your key first:

```bash
export OPENAI_API_KEY=sk-...        # macOS / Linux
$env:OPENAI_API_KEY="sk-..."        # PowerShell
```

## Examples

| Example | What it shows | Extra install | Run |
|---|---|---|---|
| [`openai-basic/`](openai-basic/main.py) | Capture a single OpenAI chat call with `@capsule.trace`, then list and export the session to a `.capsule` file. | `pip install openai` | `python examples/openai-basic/main.py` |
| [`langchain-agent/`](langchain-agent/main.py) | A billing agent capturing a LangChain LLM call via `CapsuleCallbackHandler` plus tool calls via `@capture_tool_call`. | `pip install "capsule-trace[langchain]" langchain-openai` | `python examples/langchain-agent/main.py` |

## After running

Each example prints the captured session id. Inspect or replay it with the CLI:

```bash
capsule-trace list                  # see captured sessions
capsule-trace show <session-id>     # inspect events step-by-step
capsule-trace replay <session-id>   # deterministic cassette replay (no API call)
capsule-trace export <session-id> --output bug.capsule
```
