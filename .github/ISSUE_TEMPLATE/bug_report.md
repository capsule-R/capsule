---
name: Bug Report
about: A reproducible bug in the SDK or CLI
title: "[BUG] "
labels: bug
assignees: ''
---

## Bug Description

<!-- Clear, concise description of the bug -->

## Steps to Reproduce

```python
# Minimal code example that reproduces the bug
import capsule

@capsule.trace(agent_name="test")
def my_agent():
    ...
```

## Expected Behavior

<!-- What should have happened -->

## Actual Behavior

<!-- What actually happened -->

## Error Output

```
# Paste error/traceback here
```

## Environment

- OS: [e.g., macOS 14, Ubuntu 22.04, Windows 11]
- Python version: [e.g., 3.11.7]
- capsule-sdk version: [e.g., 0.1.0]
- LLM provider SDK version: [e.g., openai==1.30.0]

## Additional Context

<!-- Attach a .capsule file if the bug relates to replay/export (remember to redact any PII first) -->
