# .capsule File Format Specification — v1.0

**Status:** Draft  
**Version:** 1.0  
**Date:** May 2026

---

## Overview

A `.capsule` file is a self-describing, compressed binary archive containing a complete, deterministically replayable record of a single AI agent execution. It is designed to be:

- **Portable** — works on any machine, any OS, any Python version ≥ 3.11
- **Self-describing** — no external metadata required to understand the contents
- **Integrity-verified** — SHA-256 hash covers all event data
- **Optionally encrypted** — customer-supplied key encrypts the entire payload
- **Compact** — zstd compression targets < 500 KB for a typical 20-step agent

---

## File Structure

A `.capsule` file is a **zstd-compressed tar archive** with the following internal layout:

```
session.capsule
├── manifest.json           # Format version, integrity hashes, producer metadata
├── session.json            # Session-level metadata (start, end, agent name, status)
├── events/                 # Ordered, immutable event log
│   ├── 0001-llm-call.json
│   ├── 0002-tool-call.json
│   ├── 0003-memory-write.json
│   └── ...
├── cassettes/              # Stored API responses for offline deterministic replay
│   ├── llm-0001.json
│   ├── tool-0002.json
│   └── ...
├── snapshots/              # Memory state snapshots (delta-compressed)
│   ├── step-0000.json      # Initial agent state
│   └── step-0010.json      # Snapshot every N steps (configurable)
└── attachments/            # Optional user-supplied supplementary files
```

---

## manifest.json

```json
{
  "capsule_version": "1.0",
  "format_spec_url": "https://capsule.dev/spec/v1.0",
  "created_at": "2026-05-27T10:30:00.000Z",
  "session_id": "ses_01HXYZ123456",
  "integrity": {
    "algorithm": "sha256",
    "events_hash": "<sha256 of concatenated sorted event JSON files>",
    "cassettes_hash": "<sha256 of concatenated sorted cassette JSON files>",
    "snapshots_hash": "<sha256 of concatenated sorted snapshot JSON files>"
  },
  "encryption": {
    "enabled": false,
    "algorithm": null,
    "key_hint": null
  },
  "compression": {
    "algorithm": "zstd",
    "level": 3
  },
  "producer": {
    "sdk_name": "capsule-python",
    "sdk_version": "0.1.0",
    "platform": "linux-x86_64",
    "python_version": "3.11.7"
  }
}
```

---

## session.json

```json
{
  "session_id": "ses_01HXYZ123456",
  "agent_name": "billing-agent-v3",
  "agent_version": "3.2.1",
  "started_at": "2026-05-27T10:30:00.000Z",
  "ended_at": "2026-05-27T10:31:42.500Z",
  "duration_ms": 102500,
  "status": "failed",
  "error": {
    "type": "ToolExecutionError",
    "message": "Refund amount exceeds policy limit",
    "stack_trace": "Traceback (most recent call last):\n  ..."
  },
  "tags": ["refund", "production", "high-value"],
  "user_metadata": {
    "customer_id": "cust_001",
    "request_id": "req_abc123"
  },
  "step_count": 23,
  "total_tokens": {
    "input": 4500,
    "output": 1200
  },
  "total_cost_usd": 0.045
}
```

**status enum:** `success | failed | in_progress | cancelled`

---

## Event Schema

Every file in `events/` is named `{NNNN}-{event_type}.json` where `NNNN` is a zero-padded step index. Events must be processed in ascending filename order.

### Common Fields (all event types)

```json
{
  "event_id": "evt_01HXYZ123",
  "session_id": "ses_01HXYZ123456",
  "step_index": 1,
  "parent_event_id": null,
  "event_type": "llm_call | tool_call | memory_write | memory_read | error | user_message",
  "timestamp": "2026-05-27T10:30:00.123Z",
  "duration_ms": 1234,
  "payload": {}
}
```

### llm_call payload

```json
{
  "provider": "openai | anthropic | google | other",
  "model": "gpt-4o",
  "model_version": "gpt-4o-2024-08-06",
  "parameters": {
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 1000,
    "seed": 42,
    "frequency_penalty": 0,
    "presence_penalty": 0
  },
  "messages": [
    {"role": "system", "content": "You are a billing assistant."},
    {"role": "user", "content": "Process a refund for order ORD-001"}
  ],
  "response": {
    "content": "I'll process that refund now.",
    "tool_calls": [],
    "finish_reason": "stop",
    "usage": {
      "prompt_tokens": 100,
      "completion_tokens": 50,
      "total_tokens": 150
    }
  },
  "cassette_ref": "cassettes/llm-0001.json"
}
```

### tool_call payload

```json
{
  "tool_name": "get_customer_balance",
  "tool_namespace": "billing.tools",
  "arguments": {"customer_id": "cust_001"},
  "result": {"balance": 1500.00, "currency": "INR"},
  "error": null,
  "execution_duration_ms": 234,
  "tool_version": "1.0.0",
  "cassette_ref": "cassettes/tool-0002.json"
}
```

### memory_write / memory_read payload

```json
{
  "memory_type": "conversation | rag_context | scratchpad | custom",
  "key": "user_intent",
  "value": "refund_request",
  "value_type": "string | number | boolean | object | array",
  "snapshot_after_ref": "snapshots/step-0003.json"
}
```

### error payload

```json
{
  "error_type": "ToolExecutionError",
  "error_message": "Refund amount exceeds policy limit",
  "stack_trace": "...",
  "is_fatal": true
}
```

---

## Cassette Files

Each cassette in `cassettes/` stores the raw API response for offline replay. The `cassette_ref` field in an event points to the corresponding cassette file.

```json
{
  "cassette_id": "llm-0001",
  "event_ref": "evt_01HXYZ123",
  "provider": "openai",
  "endpoint": "chat.completions",
  "raw_response": { ... }
}
```

During replay, the SDK intercepts outbound API calls and returns the stored `raw_response` instead of making a live request. This guarantees bit-exact reproduction.

---

## PII Redaction

Redacted fields are replaced inline with a tagged placeholder:

```json
{
  "messages": [
    {"role": "user", "content": "[REDACTED:EMAIL] requested a refund of [REDACTED:CURRENCY_AMOUNT]"}
  ],
  "redactions_applied": [
    {"type": "email", "count": 1, "pattern": "built-in"},
    {"type": "currency_amount", "count": 1, "pattern": "built-in"}
  ]
}
```

Redaction is applied at capture time and is irreversible. The `redactions_applied` field documents what was redacted without revealing the original values.

---

## Versioning

- **Major version (1.x → 2.0):** Breaking changes. SDKs must support both major versions until the previous one is deprecated (minimum 12 months).
- **Minor version (1.0 → 1.1):** Additive changes only. Older SDKs must gracefully skip unknown fields (no error on unknown keys).
- **Patch version:** Clarifications to this spec only; no format changes.

All SDKs must support at least the previous major version for backward compatibility.

---

## Integrity Verification

The `manifest.json` contains SHA-256 hashes for each directory:

```
events_hash = sha256(sorted(event_file_contents, by filename))
cassettes_hash = sha256(sorted(cassette_file_contents, by filename))
snapshots_hash = sha256(sorted(snapshot_file_contents, by filename))
```

Verification must be performed before any replay operation. A mismatch indicates file corruption or tampering.

---

## Encryption (Optional)

When `encryption.enabled = true`, the entire tar archive (before zstd compression) is encrypted using XSalsa20-Poly1305 (libsodium `secretbox`) with a customer-supplied 256-bit key. The key is never stored in the file. The `key_hint` field may contain a non-secret identifier to help the reader locate the correct key.

---

## MIME Type

`.capsule` files should be served with MIME type `application/x-capsule`.

---

## File Magic Bytes

The first 4 bytes of a valid `.capsule` file are the zstd magic bytes: `0xFD 0x2F 0xB5 0x28`.

---

*This specification is maintained at https://capsule.dev/spec/v1.0*  
*To propose changes, open a Format RFC issue on GitHub.*
