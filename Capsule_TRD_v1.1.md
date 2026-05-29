# Capsule — Technical Requirements Document (TRD)

**Project:** Capsule — Deterministic Replay & Time-Travel Debugger for AI Agents
**Document Version:** 1.5
**Date:** May 2026
**Audience:** AI Coding Agent (Implementation)
**Document Type:** Production-Grade Technical Blueprint

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.5 | May 2026 | Section 19: Design system replaced. Signal palette → Monochrome Premium. Rationale: Signal read as generic AI startup; new direction is premium/enterprise-grade closer to Linear/Vercel. Oxanium and Space Grotesk removed. Inter + Fragment Mono only. All in-document CSS token references updated. |
| 1.4 | May 2026 | Removed fixed domain ownership per founder. Both founders work across full stack based on availability. |
| 1.3 | May 2026 | Co-founder Ojasvin Yadav added. Team section added to Section 1. Section 20.7 open questions updated. YC application answers updated for two-founder story. |
| 1.2 | May 2026 | Section 19: Logo direction locked — Concept A (Signal Pill) confirmed. All TBD/pending logo references resolved. |
| 1.1 | May 2026 | Section 17: Removed week-based timeline; sprint-only format. Section 19: Full rebrand to Signal palette aligned with logo. Section 7 & 13: All infrastructure defaults to free tiers; paid tools introduced only after visible revenue growth. |
| 1.0 | May 2026 | Initial document. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Strategic Context](#2-product-vision--strategic-context)
3. [Problem Statement & Market Justification](#3-problem-statement--market-justification)
4. [Product Scope & Feature Specifications](#4-product-scope--feature-specifications)
5. [System Architecture](#5-system-architecture)
6. [The .capsule File Format Specification](#6-the-capsule-file-format-specification)
7. [Technical Stack Decisions](#7-technical-stack-decisions)
8. [Component-by-Component Implementation](#8-component-by-component-implementation)
9. [Data Models & Database Schema](#9-data-models--database-schema)
10. [API Specification](#10-api-specification)
11. [Security Protocols](#11-security-protocols)
12. [Scalability Strategy](#12-scalability-strategy)
13. [Deployment & Infrastructure](#13-deployment--infrastructure)
14. [Testing Strategy](#14-testing-strategy)
15. [Observability & Monitoring](#15-observability--monitoring)
16. [Performance Requirements](#16-performance-requirements)
17. [Build Sequence & Milestones](#17-build-sequence--milestones)
18. [Coding Standards & Repository Structure](#18-coding-standards--repository-structure)
19. [Theme & Brand System](#19-theme--brand-system)
20. [Appendix: Reference Materials](#20-appendix-reference-materials)

---

## 1. Executive Summary

### 1.1 What We Are Building

Capsule is an open-source debugging and replay platform for AI agents. It captures every action an AI agent takes in production — every LLM call, every tool invocation, every memory read/write — and packages that complete execution state into a portable `.capsule` file that can be deterministically replayed, branched, and shared across any team or platform.

### 1.2 Core Value Proposition

When an AI agent fails in production (deletes wrong data, sends wrong email, charges wrong amount), engineers today have no way to replay the exact failure because LLM outputs are non-deterministic. Capsule solves this by:

1. **Capturing** the complete deterministic state of every agent execution
2. **Replaying** failures exactly via cassette-based offline replay
3. **Branching** from any point in the execution to test alternate prompts/parameters
4. **Sharing** failures as portable `.capsule` files attachable to any bug report

### 1.3 The Three-Layer Product

| Layer | Description | License | Pricing |
|-------|-------------|---------|---------|
| **Python SDK** | Wraps any LLM call. Records to local SQLite. | Apache 2.0 (Open Source) | Free forever |
| **Cloud Platform** | Web UI, team sharing, integrations, regression library | Proprietary | $49–$599/month tiered |
| **Enterprise** | Self-hosted Docker image, SSO, audit reports, SOC 2 | Commercial license | $8–15 lakh/year |

### 1.4 Success Criteria

- **Phase 1 (Month 3):** Working SDK, 1,000+ GitHub stars, 5 production beta users
- **Phase 2 (Month 5):** Cloud platform live, 20 paying teams, ₹80,000+ MRR
- **Phase 3 (Month 9):** First enterprise contract, SOC 2 process started, ₹3,00,000+ MRR
- **Phase 4 (Month 18):** ₹10,00,000+ MRR (~₹1Cr ARR), YC application ready, 5-person team

### 1.5 The Founding Team

#### Founder 1
- **Background:** Built and launched Revastra (thrift fashion marketplace, 200+ active users on launch). Strong Python, Java, C++, AI/ML training, server management, product management.
- **Languages:** Python, Rust, Java, C++, TypeScript.
- **Why this problem:** Found the debugging gap while building AI agents personally — no existing tool could replay a failure deterministically.

#### Co-Founder — Ojasvin Yadav
- **Education:** B.Tech CSE (AI & Machine Learning), SRM IST Kattankulathur, graduating 2027. CGPA 8.69/10.
- **Technical background:** Built DecetraFi — a production-deployed full-stack Web3 decentralised crowdfunding platform on Ethereum Sepolia testnet using React, TypeScript, Tailwind CSS, Node.js, PostgreSQL, Solidity, Hardhat, and OpenZeppelin. Implemented smart contract escrow logic, MetaMask/WalletConnect auth, and automated security analysis with Slither and MythX (zero critical vulnerabilities pre-deployment). Co-built Revastra with Founder 1.
- **Finance background:** Corporate finance and treasury intern at Acmegrade (Dec 2025–Feb 2026); Capital Market Analyst intern at Pipraisers (Oct–Nov 2025). Conducted equity, commodity, and forex market research. Holds JP Morgan Investment Banking (Forage) and Deloitte Data Analytics (Forage) certifications.
- **Languages:** React, TypeScript, Tailwind CSS, Node.js, PostgreSQL, Python, Solidity.
- **Strategic value:** Finance background maps directly to Capsule's primary enterprise buyers — fintech, insurance, and legal AI companies whose compliance teams are asking "how do we prove to the regulator what our AI did?"

#### How the Team Works
Tasks are divided based on availability and time, not fixed domains. Both founders work across the full stack — whoever is available picks up the next task. Both have shipped together before on Revastra and know how to work under pressure.

---

## 2. Product Vision & Strategic Context

### 2.1 Strategic Positioning

Capsule occupies a category that currently does not exist: **deterministic replay infrastructure for AI agents.** Existing tools (LangSmith, Langfuse, Arize, AgentOps) provide tracing and observability — they record *what happened*. Capsule provides *re-execution* — the ability to deterministically run the same failure again with branching.

### 2.2 The Moat Strategy

The product is not the software — the product is the **.capsule file format**. The strategic objective is to establish `.capsule` as the de-facto industry standard for sharing AI agent bug reports. When developers attach `.capsule` files to GitHub issues the way they attach screenshots today, every debugging tool in the ecosystem must support our format. This is a standards-based moat that survives feature competition and hyperscaler entry.

### 2.3 Long-Term Vision

Over 5 years, Capsule evolves from a debugging tool into the foundational reliability layer for AI agents — the equivalent of what Sentry became for application errors and what Datadog became for infrastructure monitoring. Every team running production AI agents should consider Capsule as essential as version control.

### 2.4 Non-Goals

The following are explicitly out of scope:

- General-purpose application performance monitoring (APM)
- LLM training, fine-tuning, or model hosting
- Vector databases or RAG infrastructure
- Agent framework development (we integrate with existing frameworks)
- Real-time agent orchestration or workflow execution

---

## 3. Problem Statement & Market Justification

### 3.1 The Hair-on-Fire Problem

AI agents are now widely deployed in production environments — handling customer support, executing code, processing financial transactions, and making autonomous decisions. When these agents fail, the failure mode is fundamentally different from traditional software:

- **Non-determinism:** Running the same agent on the same input twice produces different outputs
- **State complexity:** Agents maintain conversation history, retrieved documents, intermediate variables, and tool call results across many steps
- **Provider opacity:** LLM providers do not expose internal model state, making reproduction impossible without external capture
- **Tool side-effects:** Agents call external APIs that may have changed, deleted data, or returned different results between runs

The result: when an agent fails, engineers spend hours or days guessing what happened. There is no equivalent of a stack trace, no equivalent of `pdb`, no equivalent of crash dumps. This is the gap Capsule fills.

### 3.2 Market Size & Validation

| Data Point | Source | Implication for Capsule |
|------------|--------|------------------------|
| 57.3% of orgs have AI agents in production | LangChain State of Agent Engineering 2025 | Buyer base exists and is growing |
| Only 5% of enterprise AI pilots extract real value | MIT NANDA 2025 | Reliability is the gating problem |
| >40% of agentic AI projects will be cancelled by 2027 | Gartner Forecast June 2025 | Urgency to fix observability is real |
| 62% of production teams cite observability as #1 next investment | Cleanlab 2025 | Budget is allocated; product needs to exist |
| Only 37.3% run online evals | LangChain 2025 | Massive gap between need and current tooling |

### 3.3 Competitive Landscape

Capsule competes in adjacent spaces but creates its own primary category:

| Competitor | Category | Capsule Differentiator |
|------------|----------|----------------------|
| LangSmith | Framework-locked tracing | Cross-framework, deterministic replay, branching |
| Langfuse | Open-source observability | Re-execution capability, portable format |
| AgentOps | Session recording | True deterministic replay, not video playback |
| Arize Phoenix | ML monitoring | Engineer-focused debugging, not data science |
| Braintrust | Evaluation framework | Automatic failure capture, not manual test design |
| Lucidic AI (YC W25) | Agent interpretability | Open format standard, multi-framework |

---

## 4. Product Scope & Feature Specifications

### 4.1 SDK Feature Set (Phase 1 — Month 1–3)

#### F1.1 — Automatic LLM Call Capture
**Description:** The SDK intercepts every LLM API call without requiring developers to modify their existing code (other than a single decorator).

**Acceptance Criteria:**
- Wrapper supports OpenAI Python SDK (chat.completions, responses API)
- Wrapper supports Anthropic Python SDK (messages, batch)
- Wrapper supports Google Generative AI Python SDK
- Captures: model ID, temperature, top_p, seed, max_tokens, all messages, all responses, token counts, latency, timestamp
- Zero performance impact when SDK is disabled (`CAPSULE_ENABLED=false`)
- Adds less than 5ms overhead per LLM call when enabled

#### F1.2 — Tool Call Capture
**Description:** Intercepts function/tool calls made by agents and captures inputs, outputs, and errors.

**Acceptance Criteria:**
- Supports OpenAI function calling format
- Supports Anthropic tool use format
- Supports LangChain Tool abstraction
- Captures: function name, JSON-serialized arguments, return value, execution duration, exception (if raised)
- Preserves call hierarchy (parent → child relationships)

#### F1.3 — Memory State Capture
**Description:** At each agent step, captures the complete memory and context state.

**Acceptance Criteria:**
- Captures full conversation history
- Captures retrieved documents/chunks (for RAG agents)
- Captures intermediate variables tracked by the agent framework
- Supports incremental snapshots (diff from previous state) to minimize storage
- Configurable PII redaction via regex/callback

#### F1.4 — Cassette-Based Replay
**Description:** Re-execute a captured session deterministically by replaying stored API responses instead of calling live providers.

**Acceptance Criteria:**
- 100% bit-exact reproduction of original outputs
- No external API calls required during replay
- Replay completes in < 10% of original execution time
- Supports replay on different machines, different Python versions (3.11+)

#### F1.5 — Branching Replay
**Description:** Replay from any step with modified prompts, parameters, or tool responses.

**Acceptance Criteria:**
- Branch from any captured step (by step ID or step index)
- Modify the prompt, temperature, tool response, or memory state at the branch point
- Continue execution from the branch with live LLM calls
- Compare outcomes across multiple branches

#### F1.6 — .capsule File Export
**Description:** Compress a captured session into a single portable file.

**Acceptance Criteria:**
- Single binary `.capsule` file (zstd compression)
- Target size: < 500KB for typical 20-step agent
- Self-describing format (no external metadata required)
- Cryptographic integrity hash (SHA-256)
- Optional encryption with user-supplied key

#### F1.7 — Command-Line Interface
**Description:** A complete CLI for managing capsules.

**Acceptance Criteria:**
- `capsule init` — initialize project configuration
- `capsule list` — list captured sessions
- `capsule replay <id|file>` — replay a session
- `capsule branch <id> --from-step N` — create branch
- `capsule export <id> --output file.capsule` — export to file
- `capsule import file.capsule` — import a capsule
- `capsule diff <id1> <id2>` — show differences between two sessions
- `capsule serve` — launch local web UI
- All commands support `--json` output for scripting

### 4.2 Cloud Platform Feature Set (Phase 2 — Month 3–5)

#### F2.1 — Team Accounts & Authentication
- Email/password authentication
- Google OAuth 2.0
- GitHub OAuth 2.0
- Team workspaces with role-based access control (Owner, Admin, Member, Viewer)
- API key generation per workspace

#### F2.2 — Cloud Capsule Storage
- Upload `.capsule` files to cloud storage
- Searchable metadata (agent name, error type, date range, tags)
- Configurable retention periods (30/90/180/365 days by tier)
- Automatic upload from SDK (opt-in)

#### F2.3 — Web-Based Replay UI
- Timeline view of all steps in a session
- Step-by-step inspector showing prompt, response, tools, memory
- One-click branching from any step with browser-based execution
- Outcome distribution histograms (run N times, see result spread)
- Shareable read-only replay links

#### F2.4 — Integrations
- GitHub Issues — auto-attach `.capsule` link to issues
- Slack — notifications on failure capture
- Jira — link capsules to tickets
- VS Code/Cursor extension — view and replay capsules without leaving the IDE

#### F2.5 — Billing & Subscriptions
- Stripe Checkout integration
- Three tiers: Hobby ($49/mo), Pro ($199/mo), Business ($599/mo)
- Usage-based replay compute billing (after free tier limits)
- Self-service plan changes and cancellation

### 4.3 Enterprise Feature Set (Phase 3 — Month 9+)

#### F3.1 — Self-Hosted Deployment
- Single Docker Compose file deployment
- Kubernetes Helm chart deployment
- Air-gapped operation (no external network dependencies)
- License key validation (offline)

#### F3.2 — Single Sign-On (SSO)
- SAML 2.0 support
- OpenID Connect support
- SCIM 2.0 user provisioning
- Group-based permissions sync

#### F3.3 — Audit & Compliance
- Immutable audit log of all capsule access, modification, deletion
- One-click PDF compliance report (per-agent or per-date-range)
- EU AI Act Article 12 compliance mapping (logging requirements)
- Configurable data residency (US, EU, India regions)

#### F3.4 — Regression Test Library
- Automatic test generation from production capsules
- CI/CD integration (GitHub Actions, GitLab CI, CircleCI)
- Pre-merge replay of all stored failure capsules against new code
- Detailed failure diff reports

---

## 5. System Architecture

### 5.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER ENVIRONMENT                             │
│                                                                          │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────────┐   │
│  │  Agent Code  │───▶│  Capsule SDK    │───▶│  Local SQLite Store  │   │
│  │  (Python)    │    │  (Middleware)   │    │  (~/.capsule/db)     │   │
│  └──────────────┘    └────────┬────────┘    └──────────────────────┘   │
│                               │                                          │
│                               │ (optional upload)                        │
│                               ▼                                          │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAPSULE CLOUD                                   │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────┐  │
│  │   API Gateway   │  │   FastAPI App   │  │   Next.js Web UI       │  │
│  │  (Cloudflare)   │─▶│   (Railway)     │◀─│   (Vercel)             │  │
│  └─────────────────┘  └────────┬────────┘  └────────────────────────┘  │
│                                │                                         │
│         ┌──────────────────────┼──────────────────────┐                 │
│         │                      │                      │                  │
│         ▼                      ▼                      ▼                  │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────────┐    │
│  │  PostgreSQL  │    │ Cloudflare R2   │    │   Modal Sandbox    │    │
│  │  (Supabase)  │    │  (Capsule Files)│    │  (Replay Compute)  │    │
│  │              │    │                 │    │                    │    │
│  │ • Users      │    │ • .capsule blobs│    │ • Replay execution │    │
│  │ • Workspaces │    │ • Versioned     │    │ • Branching        │    │
│  │ • Metadata   │    │ • Encrypted     │    │ • Isolated env     │    │
│  └──────────────┘    └─────────────────┘    └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Architectural Principles

#### 5.2.1 Local-First, Cloud-Optional
The SDK must work fully offline. Cloud features are additive, never required. A developer with no internet access must be able to capture, replay, and export capsules.

#### 5.2.2 Stateless Application Servers
All application servers (API, replay workers) are stateless. State lives in PostgreSQL, object storage, and ephemeral sandbox environments. This enables horizontal scaling and zero-downtime deployments.

#### 5.2.3 Event-Sourced Capture
Every captured event is immutable and append-only. The complete session state can be reconstructed by replaying events. This is the foundation of deterministic replay.

#### 5.2.4 Open Format, Closed Infrastructure
The `.capsule` file format is fully open-source and specified. The cloud infrastructure that operates on it is proprietary. This balances community adoption with commercial viability.

#### 5.2.5 Separation of Capture and Replay
The capture layer (SDK) is independent of the replay layer (engine). Either can be replaced or extended without affecting the other. This decoupling enables future innovations (e.g., custom replay engines for specific use cases).

### 5.3 Component Boundaries

| Component | Responsibility | Language | Deployment |
|-----------|---------------|----------|------------|
| **SDK** | Intercept LLM/tool calls, capture state | Python 3.11+ | PyPI package |
| **Replay Engine** | Re-execute captured sessions deterministically | Rust (Tokio) | Compiled binary embedded in SDK |
| **CLI** | User-facing command interface | Python (Click) | Same PyPI package as SDK |
| **API Server** | Cloud REST/WebSocket API | Python (FastAPI) | Railway → AWS |
| **Web UI** | User-facing dashboard | TypeScript (Next.js 14) | Vercel |
| **Replay Workers** | Cloud-based replay execution | Python on Modal | Modal serverless |
| **Database** | Metadata, accounts, audit logs | PostgreSQL 15 | Supabase → AWS RDS |
| **Object Storage** | `.capsule` file blobs | S3-compatible | Cloudflare R2 |

---

## 6. The .capsule File Format Specification

### 6.1 Format Overview

The `.capsule` file is a self-describing, compressed binary archive containing a complete, replayable record of an AI agent execution.

### 6.2 File Structure

A `.capsule` file is a zstd-compressed tar archive with the following internal structure:

```
my-session.capsule
├── manifest.json           # Format version, integrity hashes, metadata
├── session.json            # Session-level metadata (start, end, agent name)
├── events/                 # Ordered event log
│   ├── 0001-llm-call.json
│   ├── 0002-tool-call.json
│   ├── 0003-memory-write.json
│   └── ...
├── cassettes/              # Stored API responses for offline replay
│   ├── llm-0001.json
│   ├── tool-0002.json
│   └── ...
├── snapshots/              # Memory state snapshots
│   ├── step-0000.json      # Initial state
│   ├── step-0010.json      # Snapshot every N steps
│   └── ...
└── attachments/            # Optional user-supplied files
    └── ...
```

### 6.3 manifest.json Schema

```json
{
  "capsule_version": "1.0",
  "format_spec_url": "https://capsule.dev/spec/v1.0",
  "created_at": "2026-05-27T10:30:00.000Z",
  "session_id": "ses_01HXYZ123456",
  "integrity": {
    "algorithm": "sha256",
    "events_hash": "abc123...",
    "cassettes_hash": "def456...",
    "snapshots_hash": "ghi789..."
  },
  "encryption": {
    "enabled": false,
    "algorithm": null
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

### 6.4 session.json Schema

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
    "stack_trace": "..."
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

### 6.5 Event Schema (Common Fields)

Every event in `events/` must include these fields:

```json
{
  "event_id": "evt_01HXYZ123",
  "session_id": "ses_01HXYZ123456",
  "step_index": 1,
  "parent_event_id": null,
  "event_type": "llm_call | tool_call | memory_write | memory_read | error | user_message",
  "timestamp": "2026-05-27T10:30:00.123Z",
  "duration_ms": 1234,
  "payload": { ... }
}
```

### 6.6 LLM Call Event Payload

```json
{
  "event_type": "llm_call",
  "payload": {
    "provider": "openai | anthropic | google | other",
    "model": "gpt-4-turbo",
    "model_version": "gpt-4-turbo-2024-04-09",
    "parameters": {
      "temperature": 0.7,
      "top_p": 1.0,
      "max_tokens": 1000,
      "seed": 42,
      "frequency_penalty": 0,
      "presence_penalty": 0
    },
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ],
    "response": {
      "content": "...",
      "tool_calls": [...],
      "finish_reason": "stop",
      "usage": {"prompt_tokens": 100, "completion_tokens": 50}
    },
    "cassette_ref": "cassettes/llm-0001.json"
  }
}
```

### 6.7 Tool Call Event Payload

```json
{
  "event_type": "tool_call",
  "payload": {
    "tool_name": "get_customer_balance",
    "tool_namespace": "billing.tools",
    "arguments": {"customer_id": "cust_001"},
    "result": {"balance": 1500.00, "currency": "INR"},
    "error": null,
    "execution_duration_ms": 234,
    "tool_version": "1.0.0",
    "cassette_ref": "cassettes/tool-0002.json"
  }
}
```

### 6.8 Memory Operation Payload

```json
{
  "event_type": "memory_write",
  "payload": {
    "memory_type": "conversation | rag_context | scratchpad | custom",
    "key": "user_intent",
    "value": "refund_request",
    "value_type": "string",
    "snapshot_after_ref": "snapshots/step-0003.json"
  }
}
```

### 6.9 Format Versioning Strategy

- **Major version (1.x → 2.0):** Breaking changes; SDK must support both versions
- **Minor version (1.0 → 1.1):** Additive changes; older SDKs must gracefully skip unknown fields
- **All SDKs must support at least the previous major version**

### 6.10 PII Redaction

The format supports built-in PII redaction at capture time:

```json
{
  "messages": [
    {"role": "user", "content": "[REDACTED:EMAIL] requested a refund of [REDACTED:AMOUNT]"}
  ],
  "redactions_applied": [
    {"type": "email", "count": 1},
    {"type": "amount", "count": 1}
  ]
}
```

---

## 7. Technical Stack Decisions

### 7.1 Core SDK Stack

| Concern | Choice | Justification |
|---------|--------|---------------|
| Language | Python 3.11+ | 100% of AI developers use Python. Match the target audience. |
| Async runtime | asyncio (stdlib) | Required for async LLM SDK compatibility |
| Local storage | SQLite (via sqlalchemy) | Zero config, single file, durable |
| Compression | zstandard (zstd) | 2x faster than gzip, better ratios |
| Serialization | msgspec (preferred) / pydantic v2 (fallback) | Fastest JSON in Python ecosystem |
| HTTP client | httpx | Async-native, modern, replaces requests |
| CLI | Click 8+ | Most mature Python CLI framework |
| Testing | pytest + pytest-asyncio + hypothesis | Property-based testing for replay determinism |

### 7.2 Replay Engine Stack

| Concern | Choice | Justification |
|---------|--------|---------------|
| Language | Rust 1.75+ | Sub-millisecond performance, memory safety, easy cross-platform compilation |
| Async runtime | Tokio | De-facto standard for async Rust |
| Python bindings | PyO3 + maturin | Zero-cost Python ↔ Rust interop |
| Serialization | serde + serde_json | Standard Rust serialization |
| Compression | zstd crate | Same format as SDK |

### 7.3 Cloud Backend Stack

| Concern | Choice | Justification |
|---------|--------|---------------|
| API framework | FastAPI | Async-native, auto-OpenAPI, Pydantic integration |
| ORM | SQLAlchemy 2.0 (async) | Most stable Python ORM, async support |
| Migrations | Alembic | Standard for SQLAlchemy |
| Background jobs | ARQ (Redis-backed) | Simple, async-native, replaces Celery |
| Authentication | Supabase Auth (Phase 2) → Clerk or custom JWT (Phase 3 Enterprise) | Speed of build vs. flexibility tradeoff |
| Validation | Pydantic v2 | Standard with FastAPI |
| API documentation | OpenAPI 3.1 (auto-generated) | Industry standard |

### 7.4 Cloud Frontend Stack

| Concern | Choice | Justification |
|---------|--------|---------------|
| Framework | Next.js 14 (App Router) | SSR for SEO, React ecosystem, well-supported |
| Language | TypeScript 5+ (strict mode) | Type safety prevents 30% of bugs |
| Styling | Tailwind CSS 3 | Fast development without designer |
| Components | shadcn/ui + Radix UI | Accessible, customizable, no vendor lock |
| State | TanStack Query (server state) + Zustand (client state) | Best-in-class for each concern |
| Forms | React Hook Form + Zod | Performance + type-safe validation |
| Charts | Recharts | Simple, sufficient for analytics |
| Authentication client | Supabase JS Client | Matches backend choice |

### 7.5 Infrastructure Stack

| Concern | Choice | Justification |
|---------|--------|---------------|
| Database | PostgreSQL 15 (Supabase) | Open standard, mature, scales to millions of users |
| Object storage | Cloudflare R2 | Zero egress fees vs. S3 (3-5x cheaper at scale) |
| Replay compute | Modal.com | Pay-per-execution, sub-second cold start |
| API hosting | Railway free tier → Railway paid → AWS ECS | Start free, upgrade when revenue justifies |
| Frontend hosting | Vercel free tier | Native Next.js support, free tier covers Phase 1–2 |
| CDN | Cloudflare free tier | DDoS protection, global edge — free forever |
| DNS | Cloudflare free tier | Same provider as CDN, free forever |
| Email | Resend free tier (3,000/mo) | No cost until ~1,000 active users |
| Payments | Stripe (2.9% + flat fee, no monthly) | No monthly cost; fee only on successful charges |
| Analytics | PostHog free tier (1M events/mo) | Free until significant scale |
| Error monitoring | Sentry free tier (5K errors/mo) | Free for Phase 1–2 |
| Logging | Better Stack (Logtail) free tier | Free up to 1 GB/month |
| Secrets management | `.env` files local → Doppler free tier (Phase 2) → AWS Secrets Manager (Phase 4+) | Never pay until team size requires it |
| CI/CD | GitHub Actions free tier (2,000 min/mo for OSS) | Free for open-source; always sufficient for Phase 1 |

### 7.6 Compliance Tooling

**Rule:** No compliance tooling spend until enterprise customers are asking for SOC 2.

| Concern | Phase 1–2 (Free) | Phase 3+ (Revenue-Funded) |
|---------|-----------------|--------------------------|
| SOC 2 compliance | Not started — not needed | Vanta ($200/mo when first enterprise asks) |
| Vulnerability scanning | Dependabot (free, GitHub native) | Snyk paid (if Dependabot misses something) |
| Penetration testing | OWASP ZAP self-scan (free) | Cobalt.io annually from Phase 4 |

---

## 8. Component-by-Component Implementation

### 8.1 SDK: Core Wrapper Module

**Package:** `capsule.core`

**Responsibilities:**
- Provide the `@capsule.trace` decorator
- Provide context manager `with capsule.session(...)`
- Initialize a session ID and event log when entered
- Patch LLM client classes at import time (with safe fallback if SDK not installed)

**Key Classes:**

```python
# capsule/core/session.py
class Session:
    """Represents a single agent execution being captured."""
    session_id: str
    agent_name: str
    started_at: datetime
    events: list[Event]
    storage_backend: StorageBackend
    
    def capture_event(self, event: Event) -> None: ...
    def finalize(self, status: str, error: Exception | None = None) -> None: ...
    def export_capsule(self, path: Path) -> None: ...

# capsule/core/decorator.py
def trace(
    agent_name: str | None = None,
    tags: list[str] | None = None,
    redact: list[str] | None = None,
    auto_upload: bool = False,
) -> Callable: ...
```

**Implementation Notes:**
- Use `contextvars.ContextVar` to track the current session across async boundaries
- Use monkey-patching applied at module import (only patches what's actually imported)
- Capture must never raise — all exceptions inside the capture path must be swallowed and logged, never propagated to user code
- Provide a `CAPSULE_DISABLE=1` env var for emergency disable

### 8.2 SDK: Provider Integrations

**Package:** `capsule.integrations`

Submodules:
- `capsule.integrations.openai` — Patches `openai.OpenAI` and `openai.AsyncOpenAI`
- `capsule.integrations.anthropic` — Patches `anthropic.Anthropic` and `anthropic.AsyncAnthropic`
- `capsule.integrations.google` — Patches `google.generativeai`
- `capsule.integrations.langchain` — Hooks into LangChain's callback system
- `capsule.integrations.langgraph` — Native LangGraph integration

**Patching Pattern:**

```python
# capsule/integrations/openai.py
def _patched_chat_completions_create(original_method):
    @functools.wraps(original_method)
    def wrapper(self, **kwargs):
        session = get_current_session()
        if session is None:
            return original_method(self, **kwargs)
        
        event = LLMCallEvent.from_request(kwargs)
        start = time.perf_counter()
        try:
            response = original_method(self, **kwargs)
            event.complete_with_response(response, duration_ms=(time.perf_counter() - start) * 1000)
            session.capture_event(event)
            return response
        except Exception as e:
            event.complete_with_error(e, duration_ms=(time.perf_counter() - start) * 1000)
            session.capture_event(event)
            raise
    return wrapper
```

### 8.3 SDK: Storage Backend

**Package:** `capsule.storage`

**Abstract interface:**

```python
class StorageBackend(Protocol):
    def write_event(self, event: Event) -> None: ...
    def write_cassette(self, cassette_id: str, data: bytes) -> None: ...
    def write_snapshot(self, step_index: int, snapshot: dict) -> None: ...
    def read_session(self, session_id: str) -> Session: ...
    def list_sessions(self, filter: SessionFilter) -> list[SessionMetadata]: ...
    def export_to_capsule(self, session_id: str) -> bytes: ...
```

**Implementations:**
- `SQLiteBackend` — Default local storage
- `S3Backend` — For cloud uploads
- `InMemoryBackend` — For testing

### 8.4 SDK: Replay Engine Bindings

**Package:** `capsule.replay`

The Rust replay engine is exposed via PyO3 bindings:

```python
from capsule.replay import Replayer

replayer = Replayer.from_file("my_bug.capsule")
result = replayer.replay()  # Returns the final agent state
branch = replayer.branch_from_step(7, modifications={"temperature": 0.5})
branch_result = branch.replay()
```

The Rust core:
- Reads the `.capsule` archive
- Constructs an event sequence
- Provides callback hooks to the patched SDK so that during replay, LLM calls return cassette data instead of hitting providers
- Supports modification of any event before replay begins

### 8.5 CLI Module

**Package:** `capsule.cli`

Entry point in `pyproject.toml`:
```toml
[project.scripts]
capsule = "capsule.cli:main"
```

**Command Structure:**
```
capsule init                          # Initialize project
capsule list [--filter agent=X]       # List sessions
capsule show <session_id>             # Show session details
capsule replay <session_id|file>      # Replay session
capsule branch <session_id> --from-step N [--modify ...]
capsule export <session_id> --output FILE
capsule import FILE
capsule diff <id1> <id2>
capsule serve                         # Start local web UI
capsule upload <session_id>           # Upload to cloud (requires auth)
capsule login                         # Authenticate with cloud
capsule config get|set
```

### 8.6 Cloud API: Endpoints Structure

**Package:** `capsule_cloud.api`

```
GET    /api/v1/health
POST   /api/v1/auth/signup
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh

GET    /api/v1/workspaces
POST   /api/v1/workspaces
GET    /api/v1/workspaces/{id}
PATCH  /api/v1/workspaces/{id}
DELETE /api/v1/workspaces/{id}

GET    /api/v1/workspaces/{id}/members
POST   /api/v1/workspaces/{id}/members
DELETE /api/v1/workspaces/{id}/members/{user_id}

GET    /api/v1/workspaces/{id}/sessions
POST   /api/v1/workspaces/{id}/sessions          # Upload .capsule
GET    /api/v1/sessions/{id}
DELETE /api/v1/sessions/{id}
GET    /api/v1/sessions/{id}/events
GET    /api/v1/sessions/{id}/download

POST   /api/v1/sessions/{id}/replay              # Triggers Modal job
GET    /api/v1/replays/{replay_id}
POST   /api/v1/sessions/{id}/branch

GET    /api/v1/workspaces/{id}/api-keys
POST   /api/v1/workspaces/{id}/api-keys
DELETE /api/v1/api-keys/{id}

POST   /api/v1/billing/checkout
POST   /api/v1/billing/portal
POST   /api/v1/billing/webhook                   # Stripe webhook

GET    /api/v1/integrations
POST   /api/v1/integrations/github/connect
POST   /api/v1/integrations/slack/connect
```

### 8.7 Web UI Pages Structure

```
app/
├── (auth)/
│   ├── login/page.tsx
│   ├── signup/page.tsx
│   └── reset-password/page.tsx
├── (app)/
│   ├── layout.tsx                   # Authed layout with sidebar
│   ├── workspaces/
│   │   └── [id]/
│   │       ├── page.tsx              # Workspace dashboard
│   │       ├── sessions/
│   │       │   ├── page.tsx          # Session list with filters
│   │       │   └── [sessionId]/
│   │       │       ├── page.tsx      # Session detail / replay UI
│   │       │       └── branches/
│   │       │           └── [branchId]/page.tsx
│   │       ├── settings/
│   │       │   ├── general/page.tsx
│   │       │   ├── members/page.tsx
│   │       │   ├── billing/page.tsx
│   │       │   ├── api-keys/page.tsx
│   │       │   └── integrations/page.tsx
│   │       └── library/
│   │           └── page.tsx          # Regression test library
│   └── account/
│       └── page.tsx
└── (marketing)/
    ├── page.tsx                       # Landing page
    ├── docs/
    │   └── [...slug]/page.tsx
    ├── pricing/page.tsx
    └── blog/
        └── [slug]/page.tsx
```

---

## 9. Data Models & Database Schema

### 9.1 Schema Design Principles

- Use UUIDs (specifically ULID for sortability) for all primary keys
- All tables include `created_at` and `updated_at` timestamps
- Soft delete pattern (`deleted_at` nullable) for user-facing entities
- All foreign keys cascade DELETE only where data integrity requires it
- Row-Level Security (RLS) policies on all multi-tenant tables

### 9.2 Core Tables

#### users
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    email TEXT UNIQUE NOT NULL,
    email_verified_at TIMESTAMPTZ,
    full_name TEXT,
    avatar_url TEXT,
    auth_provider TEXT NOT NULL,        -- 'email' | 'google' | 'github'
    auth_provider_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
```

#### workspaces
```sql
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    owner_id TEXT NOT NULL REFERENCES users(id),
    plan_tier TEXT NOT NULL DEFAULT 'free',  -- 'free' | 'hobby' | 'pro' | 'business' | 'enterprise'
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    retention_days INT NOT NULL DEFAULT 30,
    storage_quota_gb INT NOT NULL DEFAULT 1,
    storage_used_bytes BIGINT NOT NULL DEFAULT 0,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id) WHERE deleted_at IS NULL;
```

#### workspace_members
```sql
CREATE TABLE workspace_members (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,                  -- 'owner' | 'admin' | 'member' | 'viewer'
    invited_by_id TEXT REFERENCES users(id),
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, user_id)
);
```

#### sessions
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                  -- Provided by SDK
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    agent_version TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_ms INT,
    status TEXT NOT NULL,                 -- 'success' | 'failed' | 'in_progress'
    step_count INT NOT NULL DEFAULT 0,
    total_input_tokens INT NOT NULL DEFAULT 0,
    total_output_tokens INT NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    error_type TEXT,
    error_message TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    user_metadata JSONB NOT NULL DEFAULT '{}',
    storage_path TEXT NOT NULL,           -- R2 object key
    storage_size_bytes BIGINT NOT NULL,
    integrity_hash TEXT NOT NULL,
    capsule_format_version TEXT NOT NULL,
    uploaded_by_id TEXT REFERENCES users(id),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,      -- Based on workspace.retention_days
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_sessions_workspace ON sessions(workspace_id, started_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_agent ON sessions(workspace_id, agent_name, started_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_status ON sessions(workspace_id, status, started_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_tags ON sessions USING gin(tags) WHERE deleted_at IS NULL;
```

#### replays
```sql
CREATE TABLE replays (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    initiated_by_id TEXT NOT NULL REFERENCES users(id),
    replay_mode TEXT NOT NULL,            -- 'cassette' | 'live'
    branch_from_step INT,
    modifications JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,                 -- 'queued' | 'running' | 'completed' | 'failed'
    modal_call_id TEXT,
    result_storage_path TEXT,
    duration_ms INT,
    cost_usd DECIMAL(10, 6),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_replays_session ON replays(session_id, created_at DESC);
CREATE INDEX idx_replays_workspace ON replays(workspace_id, created_at DESC);
```

#### api_keys
```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,             -- First 8 chars for display
    key_hash TEXT NOT NULL,               -- Argon2 hash of full key
    created_by_id TEXT NOT NULL REFERENCES users(id),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix) WHERE revoked_at IS NULL;
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    actor_user_id TEXT REFERENCES users(id),
    actor_api_key_id TEXT REFERENCES api_keys(id),
    actor_ip_address INET,
    action TEXT NOT NULL,                 -- 'session.created' | 'session.deleted' | 'replay.initiated' | etc.
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_workspace_time ON audit_logs(workspace_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
-- Partition by month for efficient retention pruning
```

#### integrations
```sql
CREATE TABLE integrations (
    id TEXT PRIMARY KEY DEFAULT gen_ulid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type TEXT NOT NULL,                   -- 'github' | 'slack' | 'jira'
    config JSONB NOT NULL DEFAULT '{}',
    credentials_encrypted BYTEA,          -- Encrypted via AWS KMS or libsodium sealed box
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_by_id TEXT NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.3 Row-Level Security Example

```sql
-- Sessions can only be accessed by members of the owning workspace
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY sessions_member_select ON sessions FOR SELECT
USING (
    workspace_id IN (
        SELECT workspace_id FROM workspace_members
        WHERE user_id = current_setting('app.current_user_id')::TEXT
    )
);

CREATE POLICY sessions_admin_delete ON sessions FOR DELETE
USING (
    workspace_id IN (
        SELECT workspace_id FROM workspace_members
        WHERE user_id = current_setting('app.current_user_id')::TEXT
        AND role IN ('owner', 'admin')
    )
);
```

### 9.4 Data Retention Policy

A scheduled background job runs hourly:
- Soft-deletes (`deleted_at = now()`) sessions where `expires_at < now()`
- Hard-deletes soft-deleted records after 30 days
- Removes corresponding objects from R2
- Updates workspace storage usage counters
- Writes audit log entries for compliance

---

## 10. API Specification

### 10.1 Authentication

All API endpoints (except auth endpoints and health check) require authentication via one of:

1. **JWT Bearer Token** (for web UI sessions): `Authorization: Bearer <jwt>`
2. **API Key** (for SDK uploads): `Authorization: Capsule <api_key>`

### 10.2 Request/Response Standards

- All requests/responses use JSON (`Content-Type: application/json`)
- All timestamps are ISO 8601 with timezone (e.g., `2026-05-27T10:30:00.123Z`)
- All IDs are ULID strings (26 chars)
- Pagination uses cursor-based: `?cursor=<opaque>&limit=50`
- Errors follow RFC 7807 Problem Details

### 10.3 Standard Error Response

```json
{
  "type": "https://capsule.dev/errors/insufficient-storage",
  "title": "Storage quota exceeded",
  "status": 413,
  "detail": "Workspace storage usage (5.2 GB) exceeds plan limit (5 GB). Upgrade to Pro for 50 GB.",
  "instance": "/api/v1/workspaces/wsk_abc/sessions",
  "request_id": "req_xyz123"
}
```

### 10.4 Rate Limits

| Endpoint Category | Authenticated Limit | Unauthenticated Limit |
|-------------------|---------------------|----------------------|
| Auth endpoints | 10/min | 5/min |
| Session uploads | 1000/hour | N/A |
| Read endpoints | 600/min | N/A |
| Replay triggers | Tier-dependent | N/A |
| Webhook deliveries | 100/min per integration | N/A |

Rate limit headers on every response:
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 587
X-RateLimit-Reset: 1716800400
```

### 10.5 Sample Endpoint: Upload Session

```http
POST /api/v1/workspaces/wsk_01HXYZ/sessions
Authorization: Capsule sk_live_abc123...
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="metadata"
Content-Type: application/json

{
  "session_id": "ses_01HXYZ123456",
  "agent_name": "billing-agent-v3",
  "agent_version": "3.2.1",
  "tags": ["refund", "production"],
  "auto_redact": true
}
--boundary
Content-Disposition: form-data; name="capsule"; filename="session.capsule"
Content-Type: application/octet-stream

<binary .capsule data>
--boundary--
```

Response:
```http
HTTP/1.1 201 Created
Location: /api/v1/sessions/ses_01HXYZ123456

{
  "id": "ses_01HXYZ123456",
  "workspace_id": "wsk_01HXYZ",
  "agent_name": "billing-agent-v3",
  "status": "failed",
  "step_count": 23,
  "storage_size_bytes": 423001,
  "expires_at": "2026-08-25T10:30:00.000Z",
  "uploaded_at": "2026-05-27T10:30:42.000Z",
  "view_url": "https://capsule.dev/workspaces/wsk_01HXYZ/sessions/ses_01HXYZ123456"
}
```

---

## 11. Security Protocols

Security is non-negotiable. Every decision in this section is mandatory. Cutting corners here is grounds for the AI coding agent to halt and escalate.

### 11.1 Threat Model

**Assets to protect (in priority order):**

1. Customer-uploaded `.capsule` files (may contain PII, business secrets, prompts revealing IP)
2. API keys and authentication credentials
3. User account data
4. Integration credentials (GitHub tokens, Slack webhooks)
5. Audit log integrity
6. Service availability

**Threat actors:**

- External attackers targeting customer data
- Malicious or compromised customer accounts targeting other tenants
- Insider threats (employees, contractors with system access)
- Supply chain attackers (compromised dependencies)
- Nation-state actors (relevant once enterprise customers in regulated industries are onboarded)

### 11.2 Authentication & Session Management

**Password Requirements (when email/password auth used):**
- Minimum 12 characters
- Must include 3 of: uppercase, lowercase, digit, special char
- Checked against HaveIBeenPwned API for known breached passwords
- Stored using Argon2id with parameters: `time_cost=3, memory_cost=64MB, parallelism=4`

**JWT Configuration:**
- Algorithm: EdDSA (Ed25519) — never HS256 or RS256
- Access token TTL: 15 minutes
- Refresh token TTL: 7 days
- Refresh token rotation on every use
- Refresh tokens stored hashed in database
- All tokens revocable via token revocation list (TRL)

**MFA Support (Phase 3):**
- TOTP via authenticator apps (RFC 6238)
- WebAuthn / FIDO2 hardware keys
- Recovery codes (10 single-use codes, hashed at rest)
- MFA required for Owner/Admin roles on Enterprise tier

### 11.3 API Key Management

**Generation:**
- Format: `sk_<env>_<32 bytes base62>` (e.g., `sk_live_abc123...`)
- Generated using `secrets.token_urlsafe()` for cryptographic randomness
- Full key shown to user only once at creation
- Stored as Argon2id hash in `api_keys.key_hash`
- First 8 characters stored in `api_keys.key_prefix` for display

**Scope:**
- API keys are workspace-scoped (never user-scoped or organization-wide)
- API keys have a configurable expiration date
- API keys can be limited to specific operations (read-only, upload-only, full access)

**Detection:**
- Run GitHub secret scanning partnership to detect leaked keys
- Automatically revoke any key detected in public repos
- Email workspace owner immediately on detection

### 11.4 Encryption

**At Rest:**
- Database: AES-256 encryption at the storage layer (AWS RDS / Supabase default)
- Object storage: AES-256 server-side encryption (R2 default)
- Sensitive fields (integration credentials, API key hashes) double-encrypted using:
  - Envelope encryption with AWS KMS or libsodium sealed boxes
  - Per-workspace data encryption keys (DEK) wrapped by a master key
  - Master key rotation every 90 days

**In Transit:**
- TLS 1.3 only (TLS 1.2 acceptable for clients that cannot upgrade)
- HSTS headers with `max-age=63072000; includeSubDomains; preload`
- TLS certificate via Let's Encrypt with automated renewal
- Certificate pinning in SDK for `api.capsule.dev` (Phase 3)

**End-to-End Encryption (Optional, Phase 3):**
- Customers can supply a public key during SDK config
- SDK encrypts the `.capsule` file with the customer's public key before upload
- Capsule cloud stores ciphertext only; cannot read contents
- Replay requires customer to provide private key in browser (never sent to server)

### 11.5 Multi-Tenancy Isolation

**Database Level:**
- Row-Level Security (RLS) policies on every multi-tenant table
- Every query parameterized; never construct SQL strings from user input
- Use SQLAlchemy `text()` only with bound parameters
- Tenant ID required in every query — enforced by application middleware that injects `current_setting('app.current_workspace_id')`

**Application Level:**
- Middleware that extracts workspace ID from auth context and sets PG session variable
- All ORM queries automatically filtered by workspace ID
- Cross-tenant access tests run on every PR

**Object Storage Level:**
- Storage paths include workspace ID: `{workspace_id}/{session_id}.capsule`
- Pre-signed URLs scoped to specific object paths with 5-minute expiry
- IAM policies prevent any path traversal

**Replay Sandbox Level:**
- Each replay runs in a fresh Modal sandbox
- No shared state between replays
- Network isolation by default (only outbound to LLM provider APIs)
- File system isolation (each sandbox is ephemeral)

### 11.6 Input Validation

**Every input must be validated:**
- Pydantic models for all API request bodies
- Strict type checking with no implicit conversions
- Length limits on all string fields
- Whitelisting of allowed values for enums
- Email validation via RFC 5321 + DNS MX record check
- URL validation rejecting localhost, private IPs, and AWS metadata IP

**File Upload Validation:**
- Maximum capsule file size: 100 MB (Hobby), 500 MB (Pro), 5 GB (Business)
- File format magic byte check (must start with zstd magic bytes)
- Format spec version validation
- Integrity hash verification before processing
- Quarantine queue for files that fail any check

### 11.7 Secrets Management

- Never commit secrets to git
- Use `.env.example` with placeholders only
- Production secrets in Doppler (Phase 1-2) or AWS Secrets Manager (Phase 3+)
- Secrets rotated every 90 days
- Separate secret stores for dev/staging/production
- Audit log every secret access in production

### 11.8 Dependency Security

- `pip-audit` runs on every CI build (fails on high/critical CVEs)
- `npm audit` runs on every frontend CI build
- Dependabot enabled for automated dependency PRs
- Snyk monitoring for the production lockfile
- Weekly review of all dependency updates by a human
- Lock file (`requirements.lock` for pip, `package-lock.json` for npm) committed to git
- No dependencies from unmaintained repositories (last commit > 18 months)

### 11.9 OWASP Top 10 Mitigations

| OWASP Risk | Mitigation |
|------------|------------|
| A01 Broken Access Control | RLS, role checks at every endpoint, ABAC for fine-grained perms |
| A02 Cryptographic Failures | Argon2id, EdDSA JWTs, TLS 1.3, envelope encryption |
| A03 Injection | Parameterized queries only, Pydantic input validation, escape user content in HTML |
| A04 Insecure Design | Threat modeling per feature, security review on every PR touching auth |
| A05 Security Misconfiguration | Infrastructure-as-Code (Terraform), no manual prod changes, CIS benchmarks |
| A06 Vulnerable Components | Automated scanning, weekly dep review, no abandoned packages |
| A07 Auth Failures | Account lockout after 5 failed attempts, password breach checking, MFA |
| A08 Data Integrity Failures | Signed JWTs, file hash verification, audit log immutability |
| A09 Logging Failures | Structured logging, no PII in logs, tamper-evident audit logs |
| A10 SSRF | URL allowlist for outbound webhooks, no fetching from user-provided URLs |

### 11.10 Incident Response

**Severity Levels:**
- **P0 (Critical):** Data breach, service-wide outage, exploitable vulnerability — respond within 30 minutes
- **P1 (High):** Authentication bypass, single-tenant data exposure — respond within 2 hours
- **P2 (Medium):** Degraded service, individual account compromise — respond within 24 hours
- **P3 (Low):** Minor issues — respond within 5 business days

**Required Actions on P0/P1:**
1. Acknowledge incident in incident channel (Slack #incidents)
2. Designate incident commander
3. Customer notification within 72 hours (GDPR Article 33 requirement)
4. Post-mortem published publicly within 14 days
5. Regulatory notification where required

### 11.11 Compliance Frameworks (by Phase)

- **Phase 2:** GDPR baseline (DPA, data export, deletion, breach notification)
- **Phase 3:** SOC 2 Type I
- **Phase 4:** SOC 2 Type II, HIPAA-ready (BAAs available), ISO 27001 process initiated

### 11.12 Penetration Testing

- Internal pen test before public launch (Phase 2)
- Annual external pen test starting Phase 3 (via Cobalt.io or HackerOne)
- Bug bounty program launch at Phase 4

---

## 12. Scalability Strategy

### 12.1 Scaling Targets by Phase

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Concurrent users | 100 | 1,000 | 10,000 | 100,000 |
| Sessions/day | 10,000 | 100,000 | 1M | 10M |
| Storage | 10 GB | 1 TB | 50 TB | 500 TB |
| API requests/sec | 50 | 500 | 5,000 | 50,000 |
| Replay jobs/hour | 1,000 | 50,000 | 500,000 | 5M |

### 12.2 Application Layer Scaling

**API Servers:**
- Stateless Python (FastAPI) servers behind a load balancer
- Phase 1: Single Railway service, vertical scaling
- Phase 2: Multiple Railway replicas (2–4), auto-scale on CPU > 70%
- Phase 3: Migrate to AWS ECS Fargate with auto-scaling group
- Phase 4: Multi-region deployment (US, EU, India) for data residency

**Connection Pooling:**
- PgBouncer in front of PostgreSQL (transaction-mode pooling)
- Max 100 connections per API server, 1000 total to database
- Connection lifetime: 5 minutes

### 12.3 Database Scaling

**Vertical Scaling Path:**
- Phase 1: Supabase Free (500 MB)
- Phase 2: Supabase Pro ($25/mo, 8 GB)
- Phase 3: Supabase Team or AWS RDS (db.r5.large, 16 vCPU, 128 GB RAM)
- Phase 4: AWS RDS (db.r5.4xlarge or db.r5.8xlarge with read replicas)

**Horizontal Scaling Strategy:**
- Read replicas added at Phase 3 for query-heavy endpoints
- Partition large tables (`sessions`, `audit_logs`) by month at Phase 3
- Citus or AWS Aurora Multi-Master considered at Phase 4 if vertical scaling is exhausted

**Query Performance:**
- Every query in production traced via `auto_explain` (slow query log > 100ms)
- pg_stat_statements enabled
- Weekly review of slowest queries
- Indexes added based on actual query patterns, not speculation

**Schema Migration Strategy:**
- All migrations must be backward-compatible
- Multi-step migrations for column renames/drops:
  1. Add new column
  2. Dual-write code deployed
  3. Backfill old data
  4. Switch reads to new column
  5. Stop writing to old column
  6. Drop old column

### 12.4 Object Storage Scaling

R2 scales transparently. No capacity planning needed. Strategies for cost optimization:

- Lifecycle rules: move objects older than 90 days to cold storage (or delete if retention expired)
- CDN caching for public capsule files (if customer enables sharing)
- Multipart uploads for files > 10 MB
- Pre-signed download URLs to offload bandwidth from API servers

### 12.5 Replay Compute Scaling

Modal handles auto-scaling natively. Key strategies:

- Modal functions warm-up: keep 5 warm containers per environment type
- Concurrent job limit per workspace based on plan tier
- Queue depth monitoring; auto-scale Modal concurrency on backlog
- Failed replay jobs retried up to 3 times with exponential backoff

### 12.6 Caching Strategy

**In-Memory Caching (Redis):**
- Workspace metadata (5-minute TTL)
- User permission lookups (1-minute TTL)
- API rate limit counters
- Background job queue

**HTTP Caching:**
- Static assets via Cloudflare CDN (1-year TTL with content-hash filenames)
- API responses for public endpoints (e.g., docs) cached with `Cache-Control: public, max-age=300`
- Authenticated API responses use `Cache-Control: private, no-store` by default

**Client-Side Caching:**
- TanStack Query with 5-minute stale time for list endpoints
- 30-second stale time for detail endpoints
- Optimistic updates for mutations
- Background refetch on window focus

### 12.7 Background Job Scaling

**ARQ (Redis-backed):**
- Phase 1-2: Single worker process per API server
- Phase 3: Dedicated worker fleet, separated by job priority queue
- Job types:
  - `high_priority`: User-triggered replays, deletions
  - `default`: Webhook deliveries, integration syncs
  - `low_priority`: Scheduled retention, analytics aggregation

**Job Reliability:**
- Idempotency keys on every job
- At-least-once delivery guarantee
- Dead-letter queue for jobs failing > 5 attempts
- Job results stored in Redis with 1-hour TTL

### 12.8 Frontend Scaling

Next.js on Vercel scales automatically. Optimization checklist:

- React Server Components for all data-fetching components
- Streaming SSR for slow data dependencies
- Image optimization via `next/image`
- Code splitting per route (automatic in App Router)
- Bundle analysis on every PR (warn if > 5% bundle size increase)
- Lighthouse score > 90 on every page

### 12.9 Cost Optimization

| Phase | Monthly Cloud Cost | Cost per User |
|-------|-------------------|---------------|
| Phase 1 | $50 | N/A (no users yet) |
| Phase 2 | $300 | $1.50/active user |
| Phase 3 | $3,000 | $1.00/active user |
| Phase 4 | $30,000 | $0.75/active user |

Cost discipline rules:
- Every new infrastructure component must justify its cost
- Monthly cost review with cost allocation per service
- Reserved Instances for predictable compute (Phase 3+)
- Spot Instances for batch jobs (Phase 4+)

---

## 13. Deployment & Infrastructure

### 13.1 Environments

> **Cost principle:** All environments use free-tier services until revenue is consistent. Paid tiers are only upgraded when a specific free-tier limit is actually hit, not in advance.

| Environment | Purpose | URL Pattern | Hosting (Free Tier) | Auto-Deploy From |
|-------------|---------|-------------|---------------------|------------------|
| local | Developer machines | localhost | Developer laptop | N/A |
| staging | Pre-production validation | staging.capsule.dev | Railway free tier | `main` branch |
| production | Live service | api.capsule.dev | Railway free tier → paid when traffic requires | Manual promote from staging |

> **Note:** A separate `dev` environment is skipped in Phase 1–2. Local + staging is sufficient. A dev environment is added in Phase 3 when the team grows beyond 2 people.

### 13.2 CI/CD Pipeline

**On Every PR:**
1. Run `ruff check` (Python linting)
2. Run `mypy --strict` (Python type checking)
3. Run `eslint` (TypeScript linting)
4. Run `tsc --noEmit` (TypeScript type checking)
5. Run unit tests with coverage report (must be > 80%)
6. Run integration tests
7. Run security scanning (`pip-audit`, `npm audit`, `bandit`)
8. Run secret scanning (`gitleaks`)
9. Build Docker images (no push)
10. Run dependency vulnerability check
11. Comment on PR with summary

**On Merge to `develop`:**
1. All PR checks pass
2. Build and push Docker images tagged with commit SHA
3. Deploy to `dev` environment
4. Run smoke tests against dev
5. Notify Slack on success/failure

**On Merge to `main`:**
1. All checks pass
2. Tag Docker images with version
3. Deploy to `staging`
4. Run full integration test suite against staging
5. Run synthetic load test (1000 RPS for 5 minutes)
6. Hold for manual approval to promote to production

**Production Deploy:**
1. Manual approval by repository admin
2. Database migrations run (if any) with locking strategy
3. Blue-green deployment (Phase 3+) or rolling deployment
4. Synthetic transaction test post-deploy
5. Auto-rollback if error rate > 1% for 5 minutes post-deploy

### 13.3 Infrastructure as Code

All cloud infrastructure declared in Terraform:

```
infra/
├── modules/
│   ├── network/
│   ├── database/
│   ├── storage/
│   ├── compute/
│   └── monitoring/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── README.md
```

No manual changes to production infrastructure. All changes via PR to `infra/` repo.

### 13.4 Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 15 minutes

**Backup Strategy:**
- PostgreSQL: Continuous WAL backup to S3 (point-in-time recovery for 30 days)
- Daily full database backup retained for 90 days
- Object storage (R2): Versioning enabled, lifecycle rules to delete old versions after 30 days
- Configuration backups (Terraform state) stored in version-controlled S3 bucket

**DR Testing:**
- Quarterly DR drill: restore database to a separate environment and verify
- Annual full failover test (Phase 4+)

### 13.5 Monitoring & Alerting

See [Section 15: Observability & Monitoring](#15-observability--monitoring).

---

## 14. Testing Strategy

### 14.1 Test Pyramid

```
                    ▲
                   / \
                  / E2E\         5%   — Playwright, real browsers
                 /─────\
                /Integration\    20%  — pytest with real DB, mock LLMs
               /───────────\
              /  Unit Tests \    75%  — pytest, fully isolated
             /───────────────\
```

### 14.2 SDK Testing

**Unit Tests (`tests/unit/`):**
- Every public function/class has at least one test
- Edge cases: empty inputs, None values, very large inputs, unicode, malformed data
- Mock all external dependencies (LLM APIs, file I/O where possible)
- Use `hypothesis` for property-based testing of:
  - Capsule serialization → deserialization roundtrip
  - Replay determinism (capture session, replay, verify byte-exact match)
  - Compression/decompression

**Integration Tests (`tests/integration/`):**
- Test against real (but throwaway) SQLite databases
- Test against recorded LLM responses (using `vcr.py` or similar)
- Test full capture-export-import-replay cycle
- Test framework integrations (LangChain, LangGraph) with real framework versions

**Cross-Version Compatibility Tests:**
- Capsules created by SDK v1.0 must be replayable by SDK v1.1, v1.2, etc.
- Run against a corpus of historical capsule files on every release

### 14.3 Cloud Backend Testing

**Unit Tests:**
- Service layer logic in isolation
- Mock database, storage, external APIs
- Pydantic validation tests for all request/response models

**Integration Tests:**
- Spin up test PostgreSQL (via testcontainers)
- Spin up test MinIO (S3-compatible) for object storage
- Spin up test Redis for jobs
- Run full API request/response cycles
- Verify RLS policies prevent cross-tenant access

**Contract Tests:**
- OpenAPI spec consumed by frontend; ensure frontend never depends on undocumented fields
- Schemathesis-generated tests verifying every endpoint matches the OpenAPI spec

### 14.4 End-to-End Tests

**Playwright Test Suites (`tests/e2e/`):**
- User signup flow
- Workspace creation
- Capsule upload from CLI → view in web UI
- Replay flow with branching
- Subscription upgrade flow
- API key generation and use

**Run Frequency:**
- Critical paths run on every staging deploy
- Full suite runs nightly

### 14.5 Load Testing

**Tool:** k6 (script-based load tests)

**Scenarios:**
- Constant 100 RPS for 30 minutes (steady-state)
- Ramp from 0 to 1000 RPS over 5 minutes (burst)
- 10 RPS sustained for 6 hours (long-running stability)

**Run Frequency:**
- Before each Phase milestone
- Before any major architecture change

### 14.6 Chaos Engineering (Phase 3+)

**Scenarios:**
- Random pod kill
- Database connection exhaustion
- Object storage temporary unavailability
- Network latency injection
- Disk full simulation

**Tool:** Chaos Mesh (Kubernetes) or custom scripts on Railway

### 14.7 Security Testing

- SAST: Bandit (Python), ESLint security plugin (TypeScript)
- DAST: OWASP ZAP scan on staging weekly
- Dependency scanning: pip-audit, npm audit, Snyk
- Secret scanning: gitleaks on every commit
- Authentication fuzz testing: ensure no auth bypass via malformed JWTs

---

## 15. Observability & Monitoring

### 15.1 The Three Pillars

**Metrics → Logs → Traces** — every production issue must be diagnosable by following this chain.

### 15.2 Metrics (Prometheus + Grafana, or Datadog at scale)

**Application Metrics:**
- HTTP request duration (p50, p95, p99) per endpoint
- HTTP request rate per endpoint
- HTTP error rate per endpoint (4xx, 5xx separated)
- Background job duration and success rate per job type
- Replay job duration and success rate
- Authentication failure rate

**Business Metrics:**
- Active workspaces (DAU, WAU, MAU)
- Sessions uploaded per hour
- Storage usage by workspace
- Replay jobs per workspace
- New signups, conversions, churns
- MRR, ARR (synced from Stripe)

**Infrastructure Metrics:**
- Database connection pool usage
- Database query duration
- Redis hit rate
- R2 request rate and latency
- Modal sandbox start time

### 15.3 Logging (Structured JSON)

**Log Format:**
```json
{
  "timestamp": "2026-05-27T10:30:00.123Z",
  "level": "INFO",
  "service": "api",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "usr_xyz",
  "workspace_id": "wsk_abc",
  "request_id": "req_123",
  "message": "Session uploaded",
  "session_id": "ses_456",
  "size_bytes": 423001,
  "duration_ms": 142
}
```

**Logging Rules:**
- Never log: passwords, API keys, JWTs, full prompt contents (unless explicitly enabled)
- Always log: request_id, user_id (if authenticated), workspace_id, action, outcome
- Use INFO for business events, WARN for recoverable issues, ERROR for failures requiring investigation
- DEBUG logs only in development; never in production

**Log Aggregation:**
- Phase 1–2: Better Stack (Logtail) free tier — 1 GB/month, zero cost
- Phase 3 (only if free tier is exhausted): Self-hosted Grafana Loki on Railway — still cheap
- Phase 4+: Datadog Logs or Axiom, funded by revenue

### 15.4 Tracing (OpenTelemetry)

- All API requests instrumented with OpenTelemetry
- Trace context propagated through background jobs
- Trace context propagated to Modal replay jobs
- 10% sampling rate in production (100% for errors)
- Phase 1–2: Sentry Performance (free tier, 10K transactions/month)
- Phase 3+: Self-hosted Grafana Tempo or Datadog APM — only when Sentry free tier is exhausted

### 15.5 Error Tracking (Sentry)

- All unhandled exceptions captured
- User context attached (user_id, workspace_id)
- Source maps uploaded for frontend errors
- Performance monitoring enabled for slow transactions
- Release tracking integrated with deploys

### 15.6 Alerting

**Alert Channels:**
- Phase 1–2: Uptime Robot free tier (50 monitors) for uptime + email alerts. No PagerDuty until team > 2.
- Phase 3+: BetterUptime or PagerDuty when 24/7 on-call rotation is needed
- Slack free workspace: #alerts channel for P2/P3
- Email: Resend free tier for warning digests

**Sample Alert Rules:**

| Metric | Threshold | Severity | Action |
|--------|-----------|----------|--------|
| 5xx rate | > 1% for 5 min | P1 | Page on-call |
| API p99 latency | > 2s for 10 min | P2 | Slack alert |
| Database CPU | > 80% for 10 min | P2 | Slack alert |
| Database connections | > 90% of pool | P1 | Page on-call |
| Failed authentication | > 100/min from single IP | P2 | Auto-block IP |
| Storage usage | > 80% of plan limit | P3 | Notify customer |
| Replay job failure rate | > 5% for 15 min | P2 | Slack alert |
| Stripe webhook failure | Any | P1 | Page on-call |
| SSL cert expiry | < 14 days | P2 | Slack alert |

### 15.7 Status Page

- Phase 1–2: Uptime Robot free status page at `status.capsule.dev` — zero cost
- Phase 3+: Instatus free tier or BetterUptime status page
- Updated automatically based on monitoring metrics
- Manual updates for planned maintenance
- Subscribe via email for status notifications

### 15.8 Customer-Facing Observability

Workspaces can view in the UI:
- Their own usage metrics
- Their session capture rate
- Their replay job durations
- Their API key usage

---

## 16. Performance Requirements

### 16.1 SDK Performance Targets

| Operation | Target | Hard Limit |
|-----------|--------|-----------|
| LLM call wrapping overhead | < 1 ms | 5 ms |
| Event serialization (per event) | < 0.5 ms | 2 ms |
| SQLite write (per event) | < 5 ms | 20 ms |
| Session finalization | < 100 ms | 500 ms |
| Capsule export (20-step session) | < 500 ms | 2 s |
| Cassette replay (per step) | < 10 ms | 50 ms |
| Branching replay setup | < 200 ms | 1 s |

### 16.2 Cloud Platform Performance Targets

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| GET /sessions | 50 ms | 200 ms | 500 ms |
| POST /sessions (upload) | 300 ms | 1 s | 3 s |
| GET /sessions/{id} | 30 ms | 100 ms | 300 ms |
| POST /sessions/{id}/replay (queue) | 100 ms | 300 ms | 1 s |
| Replay execution (20 steps) | 5 s | 15 s | 30 s |
| Web UI page load (LCP) | 1 s | 2 s | 3 s |
| Web UI interaction (INP) | 100 ms | 200 ms | 500 ms |

### 16.3 Availability Targets

| Service | Availability SLA | Allowed Downtime |
|---------|-----------------|------------------|
| API (Phase 1-2) | 99.5% | 3.6 hours/month |
| API (Phase 3) | 99.9% | 43 minutes/month |
| API (Phase 4 Enterprise) | 99.95% | 21 minutes/month |
| Replay compute | 99% | 7 hours/month |
| Web UI | 99.5% | 3.6 hours/month |

---

## 17. Build Sequence & Milestones

This section maps all deliverables to sprints and phases. No week-level granularity is specified — the AI coding agent works through sprints in order and moves to the next when the Definition of Done is satisfied.

### Phase Overview

| Phase | Sprints | Goal | Revenue Target |
|-------|---------|------|----------------|
| **Phase 1 — Build** | Sprint 1–4 | Working OSS SDK, CLI, replay engine | $0 (pre-revenue) |
| **Phase 2 — Launch** | Sprint 5–7 | Cloud platform live, paying users | $0 → ₹80K MRR |
| **Phase 3 — Grow** | Sprint 8–10 | Integrations, enterprise pipeline | ₹80K → ₹5L MRR |
| **Phase 4 — Scale** | Sprint 11+ | SOC 2, self-hosted, YC-ready | ₹5L → ₹1Cr ARR |

---

### Phase 1 — Build

#### Sprint 1: Project Foundation

**Goal:** Repository is set up, all tooling works, nothing is broken before coding begins.

**Deliverables:**
- [ ] Monorepo structure created (see Section 18)
- [ ] All linting, formatting, type-checking configured
- [ ] GitHub Actions CI pipeline configured (lint, test, type check)
- [ ] Pre-commit hooks configured (ruff, mypy, prettier, eslint)
- [ ] License files added (Apache 2.0 for SDK, Proprietary for cloud)
- [ ] CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md added
- [ ] Initial `.capsule` format spec document drafted and committed to `docs/spec/`

**Exit Criteria:** CI runs green on an empty commit. All tooling commands execute without error on a fresh checkout.

---

#### Sprint 2: SDK Core

**Goal:** A developer can wrap their OpenAI or Anthropic calls with one decorator and see captured events in their local SQLite database.

**Deliverables:**
- [ ] `capsule.core.Session` class implemented
- [ ] `@capsule.trace` decorator implemented
- [ ] `contextvars.ContextVar` session tracking (async-safe)
- [ ] SQLite storage backend implemented
- [ ] Event model definitions complete (all types from Section 6)
- [ ] OpenAI integration — sync + async (`chat.completions`, `responses`)
- [ ] Anthropic integration — sync + async (`messages`)
- [ ] Unit test coverage > 80% on all capture logic
- [ ] `CAPSULE_DISABLE=1` env var disables all capture with zero overhead
- [ ] First end-to-end example: `examples/openai-basic/` working

**Exit Criteria:** Running the `openai-basic` example produces a populated SQLite database with correctly structured events.

---

#### Sprint 3: Replay Engine

**Goal:** A developer can replay a captured session byte-for-byte using a cassette, and branch from any step.

**Deliverables:**
- [ ] Rust project initialised with maturin + PyO3
- [ ] Cassette-based offline replay implemented (no external API calls)
- [ ] Live deterministic replay (temperature=0, same seed)
- [ ] Branching from arbitrary step index implemented
- [ ] Memory snapshot serialisation / restoration working
- [ ] Property-based tests (Hypothesis): 10,000+ random sessions replay deterministically
- [ ] Python bindings: `from capsule.replay import Replayer` works

**Exit Criteria:** A captured session replayed 100 times in cassette mode produces bit-exact identical results every time.

---

#### Sprint 4: CLI, Export & SDK Polish

**Goal:** The complete user-facing SDK experience is ready to publish on PyPI and launch on GitHub.

**Deliverables:**
- [ ] All CLI commands implemented (see Section 8.5)
- [ ] `.capsule` file export with zstd compression and SHA-256 integrity hash
- [ ] `.capsule` file import working cross-platform (Linux, macOS, Windows)
- [ ] Tool call interception — OpenAI function calling + Anthropic tool use formats
- [ ] LangChain integration via callback handler
- [ ] LangGraph native integration via StateGraph hook
- [ ] Google Generative AI integration
- [ ] PyPI package publishable — `pip install capsule-sdk` works
- [ ] Documentation site (Mintlify free tier) with quickstart guide
- [ ] README complete — problem, GIF demo, install, 3 code examples
- [ ] 5 private beta users testing on real agent failures

**Exit Criteria:** Any developer can run `pip install capsule-sdk`, add `@capsule.trace`, and get a working `.capsule` file in under 5 minutes from a cold start.

---

### Phase 2 — Launch

#### Sprint 5: Cloud Foundation

**Goal:** The cloud backend exists and the SDK can upload capsules to it via API key.

**Deliverables:**
- [ ] Supabase project created (free tier), schema applied via Alembic
- [ ] FastAPI application with auth middleware (JWT + API key)
- [ ] User signup / login / logout endpoints
- [ ] Workspace creation and management endpoints
- [ ] API key generation endpoints
- [ ] Cloudflare R2 bucket configured (free tier)
- [ ] Session upload endpoint — accepts `.capsule` binary, stores to R2
- [ ] Modal.com free tier sandbox running first test replay
- [ ] Railway free tier deployment of API server
- [ ] SDK `auto_upload=True` flag working end-to-end

**Exit Criteria:** `capsule upload <session_id>` succeeds and the session is visible in the database.

---

#### Sprint 6: Web UI

**Goal:** A logged-in user can see their sessions, inspect every step, and trigger a replay from the browser.

**Deliverables:**
- [ ] Next.js 14 project, deployed on Vercel free tier
- [ ] Authentication flow (signup, login, Google OAuth via Supabase)
- [ ] Workspace dashboard — session list with search + filters
- [ ] Session detail view — timeline of all events with full payloads
- [ ] Replay UI — one-click cassette replay, step-by-step viewer
- [ ] Branch UI — pick a step, modify params, run live replay
- [ ] Settings pages — general, members (invite by email), API keys
- [ ] Stripe Checkout — Hobby ($49) and Pro ($199) plans

**Exit Criteria:** A user can sign up, upload a capsule from the CLI, view it in the browser, and replay it — all in one flow without touching code.

---

#### Sprint 7: Launch & First Paying Users

**Goal:** Public launch executed, first paying customers signed up.

**Deliverables:**
- [ ] GitHub repository public — clean README, examples folder, CONTRIBUTING guide
- [ ] Show HN post submitted (Tuesday–Thursday, 8:30–10:30pm IST)
- [ ] Product Hunt listing scheduled
- [ ] LangChain Discord, CrewAI Discord, r/LocalLLaMA posts
- [ ] Technical blog post on dev.to: "Why you can't debug AI agents like normal code"
- [ ] Waitlist email sequence configured in Resend (free tier)
- [ ] GitHub integration — auto-attach `.capsule` links to issues via GitHub App
- [ ] Slack integration — post to channel on agent failure
- [ ] VS Code extension published on Marketplace (free)
- [ ] Marketing landing page live at `capsule.dev` or chosen domain

**Exit Criteria:** 20 paying teams signed up. 200+ GitHub stars. ₹80,000+ first month revenue.

---

### Phase 3 — Grow

#### Sprint 8: Integration Depth & Enterprise Pipeline

**Goal:** Capsule is integrated with the 3 most popular agent frameworks. First enterprise conversation started.

**Deliverables:**
- [ ] LangGraph deep integration (native `add_capsule_tracing()` for StateGraph)
- [ ] OpenAI Agents SDK integration
- [ ] Langfuse "Export to Capsule" integration (open PR to their repo)
- [ ] GitHub Actions action: `capsule-replay-tests` for CI/CD pipelines
- [ ] Identify 20 enterprise target companies (fintech, legal AI, healthcare AI)
- [ ] Cold outreach template written and first 20 emails sent
- [ ] First enterprise demo call completed

**Exit Criteria:** At least 2 framework integrations live. First enterprise demo scheduled.

---

#### Sprint 9: Teams Feature & Regression Library

**Goal:** Teams can build a regression test suite automatically from past production failures.

**Deliverables:**
- [ ] Regression test library — all stored capsules replayable as a test suite
- [ ] CI/CD integration — `capsule test --against-library` runs against a branch
- [ ] PR comment bot — posts replay results directly on GitHub PRs
- [ ] Slack failure alerts — "Agent failed in prod, here's the capsule" auto-posted
- [ ] Business plan tier ($599/mo) live with unlimited team members + CI/CD
- [ ] First enterprise contract signed (₹2–4 lakh/year pilot)

**Exit Criteria:** One team has Capsule running in their CI pipeline. One enterprise pilot contract signed.

---

#### Sprint 10: First Hire & SOC 2 Start

**Goal:** Company is no longer a solo operation. Compliance process started.

**Deliverables:**
- [ ] First developer hire onboarded (backend or full-stack)
- [ ] IP assignment + employment contract signed
- [ ] Vanta account set up — SOC 2 Type I preparation started
- [ ] Access control, incident response, and vulnerability scanning policies written
- [ ] 10 enterprise controls implemented per Vanta checklist
- [ ] Conference talk submitted (AI Engineer Summit, PyCon India, or NASSCOM)

**Exit Criteria:** Two-person team. SOC 2 audit in progress. Revenue ≥ ₹3L/month.

---

### Phase 4 — Scale

#### Sprint 11: SOC 2 & Self-Hosted Tier

**Goal:** Enterprise customers can answer "yes" to security questionnaires. Large enterprises can run Capsule inside their own VPC.

**Deliverables:**
- [ ] SOC 2 Type I certificate obtained
- [ ] Self-hosted Docker Compose package — single-command deploy to any server
- [ ] Kubernetes Helm chart for enterprise DevOps teams
- [ ] License key validation for self-hosted deployments
- [ ] Air-gapped mode (no external network dependencies in replay)
- [ ] Enterprise pricing tier live — ₹8–15 lakh/year

**Exit Criteria:** One customer running Capsule self-hosted in their private VPC. SOC 2 cert published on website.

---

#### Sprint 12: Community & Format Standard

**Goal:** `.capsule` is on its way to being an industry standard, not just a Capsule product feature.

**Deliverables:**
- [ ] Discord server launched — `#share-your-capsules`, `#format-rfc`, `#integrations`
- [ ] Formal proposal sent to Langfuse, Arize, and Braintrust for native `.capsule` support
- [ ] Open RFC process for `.capsule` format v1.1 (community-driven)
- [ ] KernelBench-adjacent: publish "AgentReplayBench" — open benchmark suite for replay fidelity
- [ ] Conference talk delivered

**Exit Criteria:** At least 2 external tools support `.capsule` natively. 500+ Discord members.

---

#### Sprint 13: YC Application & Fundraising Prep

**Goal:** Application submitted with strong traction data.

**Deliverables:**
- [ ] Monthly revenue ≥ ₹8L and growing ≥ 15% MoM for 3 consecutive months
- [ ] 10+ paying enterprise or Pro customers
- [ ] "Very disappointed" user survey: ≥ 40% say they'd be very disappointed if Capsule shut down
- [ ] GitHub stars ≥ 1,000
- [ ] YC application submitted (ycombinator.com/apply)
- [ ] Investor pitch deck prepared (10 slides)
- [ ] Warm intro to at least 2 YC partners via alumni network

**Exit Criteria:** YC application submitted. Seed round conversations started with 3+ India-based funds.

---

### 17.9 Definition of Done

A feature is "done" when:
1. Code is reviewed and merged to `develop`
2. Unit tests written with coverage > 80% for new code
3. Integration tests pass
4. Documentation updated
5. Type checking passes (`mypy --strict` for Python, `tsc --noEmit` for TS)
6. No new linting warnings introduced
7. No new security vulnerabilities introduced
8. Performance benchmarks not regressed
9. Deployed to staging and smoke-tested
10. Feature flag created (if user-facing) for gradual rollout

---

## 18. Coding Standards & Repository Structure

### 18.1 Monorepo Structure

```
capsule/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── release-sdk.yml
│   │   └── deploy-cloud.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── spec/
│   │   └── capsule-format-v1.md
│   ├── architecture/
│   ├── guides/
│   └── api/
├── packages/
│   ├── sdk/                          # Python SDK
│   │   ├── src/capsule/
│   │   │   ├── __init__.py
│   │   │   ├── core/
│   │   │   ├── integrations/
│   │   │   ├── storage/
│   │   │   ├── replay/               # PyO3 bindings
│   │   │   └── cli/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── LICENSE                   # Apache 2.0
│   ├── replay-engine/                # Rust replay engine
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Cargo.toml
│   │   └── README.md
│   ├── cloud-api/                    # FastAPI backend
│   │   ├── src/capsule_cloud/
│   │   ├── tests/
│   │   ├── migrations/               # Alembic
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── cloud-web/                    # Next.js frontend
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── vscode-extension/             # VS Code extension
│       ├── src/
│       └── package.json
├── infra/                            # Terraform IaC
│   ├── modules/
│   └── environments/
├── examples/                         # Working code examples
│   ├── openai-basic/
│   ├── langchain-agent/
│   └── langgraph-multi-agent/
├── scripts/                          # Dev/ops scripts
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── CHANGELOG.md
```

### 18.2 Python Style Guide

- **Formatter:** `ruff format` (replaces black)
- **Linter:** `ruff check` with rules `E, F, W, I, N, UP, B, C4, SIM, TCH, RET`
- **Type Checker:** `mypy --strict`
- **Docstring Style:** Google style
- **Maximum Line Length:** 100 characters
- **Import Order:** stdlib → third-party → first-party → local (enforced by ruff)
- **Naming Conventions:**
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`
- **Type Hints:** Required on all public functions and methods
- **Error Handling:** Never use bare `except:`. Always specify exception types.

### 18.3 TypeScript Style Guide

- **Formatter:** `prettier` with 2-space indent, single quotes, no semicolons
- **Linter:** `eslint` with `@typescript-eslint`, `eslint-plugin-react`, `eslint-plugin-security`
- **Type Checker:** `tsc --strict --noEmit`
- **Maximum Line Length:** 100 characters
- **Naming Conventions:**
  - Components: `PascalCase`
  - Hooks: `useXxx` (camelCase)
  - Functions/variables: `camelCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Types/Interfaces: `PascalCase`
- **No `any`** — use `unknown` if type is genuinely unknown
- **Prefer `interface` over `type` for object shapes** (better error messages)

### 18.4 Rust Style Guide

- **Formatter:** `cargo fmt` with default config
- **Linter:** `cargo clippy -- -D warnings`
- **Edition:** 2021
- **Documentation:** All public items must have doc comments
- **Error Handling:** Use `thiserror` for library errors, `anyhow` for application errors
- **No `unwrap()` in production code paths** (except in tests)

### 18.5 Git Conventions

**Branch Naming:**
- `feature/short-description`
- `fix/short-description`
- `chore/short-description`
- `docs/short-description`

**Commit Message Format (Conventional Commits):**
```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
```
feat(sdk): add automatic capture for Anthropic SDK
fix(cloud-api): prevent cross-tenant session access
docs(spec): clarify cassette resolution algorithm
chore(deps): bump fastapi to 0.110.0
```

**PR Requirements:**
- Title must follow Conventional Commits format
- Description must include: what, why, how to test
- Linked issue (if applicable)
- Screenshots for UI changes
- Two approvals required (one engineer + one security review for changes to auth/data)

---

## 19. Theme & Brand System

The **Monochrome Premium** palette is the authoritative design system for Capsule. It replaces the previous Signal (indigo) palette.

**Rationale for change:** The Signal palette read as a generic AI startup — indigo CTAs, glowing accents, cyan highlights. Every LLM observability tool in 2026 looks like that. The new direction is premium, minimal, and enterprise-grade — closer to Linear, Vercel, and Raycast than to AI tooling. No color. No gradients. Pure monochrome confidence.

> **Logo status: LOCKED — Concept A (Signal Pill).** The logo mark retains its shape. The pill color updates from indigo `#6366F1` to white `#F5F5F5` on dark backgrounds (and black `#0A0A0A` on light backgrounds). Full spec in `Capsule_Logo_Brief_v1.0.md`. SVG must be regenerated to reflect the new palette and committed to `packages/cloud-web/public/brand/logo.svg` during Sprint 1.

### 19.1 Design Philosophy

- **Pure dark, no color:** The background is near-black (`#0A0A0A`). There are no color accents — no indigo, no cyan, no purple. Everything communicates through contrast, spacing, and typography.
- **White is the accent:** The only "brand color" is white. CTAs, highlights, active states — all white on dark. This is intentional restraint.
- **Monospace as identity:** `Fragment Mono` is the second typeface and carries as much brand weight as `Inter`. Every metric, timestamp, ID, and data point uses it. The monospace texture is what makes Capsule feel like a tool built by engineers for engineers.
- **Enterprise premium:** The aesthetic signals that this is serious infrastructure, not a weekend project. Potential buyers in regulated industries — banks, insurance, legal AI — should feel that Capsule is as trustworthy as the systems they already run.

### 19.2 Color Tokens

```css
:root {
  /* ── BACKGROUNDS ── */
  --bg-base:        #0A0A0A;   /* Page background — true near-black */
  --bg-card:        #111111;   /* Card backgrounds, sidebars */
  --bg-elevated:    #1A1A1A;   /* Modals, dropdowns, popovers */
  --bg-hover:       #222222;   /* Hover states on interactive elements */

  /* ── BORDERS ── */
  --border-subtle:  #1F1F1F;   /* Hairline dividers, table rows */
  --border-default: #2A2A2A;   /* Card borders, input borders */
  --border-strong:  #3A3A3A;   /* Hover borders, focus rings */

  /* ── TEXT ── */
  --text-primary:   #F5F5F5;   /* Headings, primary labels — main reading color */
  --text-secondary: #A0A0A0;   /* Descriptions, secondary labels */
  --text-tertiary:  #606060;   /* Placeholders, disabled, timestamps */
  --text-inverse:   #0A0A0A;   /* Text on white/light backgrounds */

  /* ── ACCENT (white only) ── */
  --accent:         #F5F5F5;   /* Primary CTA background, active states */
  --accent-hover:   #E0E0E0;   /* CTA hover state */

  /* ── SEMANTIC ── */
  --success:  #22C55E;   /* Replay success, test pass, health OK */
  --warn:     #F59E0B;   /* Stale capsule, approaching limit */
  --error:    #EF4444;   /* Agent failure, exception, test fail */
  --replay:   #E2E8F0;   /* Replay action elements — light grey, not cyan */

  /* ── MONOSPACE SURFACE ── */
  --mono-bg:   #141414;   /* Background behind code blocks, terminal output */
  --mono-text: #D4D4D4;   /* Text inside code blocks */
}
```

### 19.3 Tailwind CSS Token Mapping

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        bg: {
          base:     '#0A0A0A',
          card:     '#111111',
          elevated: '#1A1A1A',
          hover:    '#222222',
        },
        border: {
          subtle:   '#1F1F1F',
          default:  '#2A2A2A',
          strong:   '#3A3A3A',
        },
        text: {
          primary:   '#F5F5F5',
          secondary: '#A0A0A0',
          tertiary:  '#606060',
          inverse:   '#0A0A0A',
        },
        accent:   '#F5F5F5',
        success:  '#22C55E',
        warn:     '#F59E0B',
        error:    '#EF4444',
        replay:   '#E2E8F0',
        mono: {
          bg:   '#141414',
          text: '#D4D4D4',
        },
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['Fragment Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
}
```

### 19.4 Typography

Two fonts only. No display font.

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| All UI text, body, headings, buttons, labels | `Inter` | 400, 500, 600 | Everything except code and data |
| Code, IDs, metrics, timestamps, hero data points | `Fragment Mono` | 400, 500 | Anything that is a number, hash, key, or machine-generated string |

`Inter` is available on Google Fonts (free). `Fragment Mono` is available on Google Fonts (free).

**Removed fonts:** Oxanium (too stylized, not enterprise), Space Grotesk (replaced by Inter), Space Mono (consolidated into Fragment Mono).

```html
<link href="https://fonts.googleapis.com/css2?
  family=Inter:wght@400;500;600&
  family=Fragment+Mono:wght@400;500&
  display=swap" rel="stylesheet">
```

**Typography scale:**

```css
/* Headings — Inter, no display font */
.h1 { font-family: 'Inter', sans-serif; font-size: 32px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.5px; }
.h2 { font-family: 'Inter', sans-serif; font-size: 24px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.3px; }
.h3 { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 500; color: var(--text-primary); }

/* Body */
.body { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 400; color: var(--text-secondary); line-height: 1.6; }

/* Labels */
.label { font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; color: var(--text-tertiary); letter-spacing: 0.5px; text-transform: uppercase; }

/* Monospace — data, IDs, metrics */
.mono { font-family: 'Fragment Mono', monospace; font-size: 13px; font-weight: 400; color: var(--mono-text); }
.mono-hero { font-family: 'Fragment Mono', monospace; font-size: 48px; font-weight: 500; color: var(--text-primary); }
```

### 19.5 Component Patterns

```css
/* ── Cards ── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: 8px;
}
.card:hover {
  border-color: var(--border-strong);
}

/* ── Primary CTA (white button) ── */
.btn-primary {
  background: var(--accent);          /* #F5F5F5 */
  color: var(--text-inverse);         /* #0A0A0A */
  border: none;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  cursor: pointer;
}
.btn-primary:hover {
  background: var(--accent-hover);    /* #E0E0E0 */
}

/* ── Secondary / Ghost button ── */
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
}
.btn-secondary:hover {
  border-color: var(--border-strong);
  background: var(--bg-hover);
}

/* ── Replay action button (light grey, not cyan) ── */
.btn-replay {
  background: var(--bg-elevated);
  color: var(--replay);               /* #E2E8F0 */
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-family: 'Fragment Mono', monospace;
  font-size: 13px;
  font-weight: 500;
}
.btn-replay:hover {
  border-color: var(--border-strong);
  background: var(--bg-hover);
}

/* ── Input fields ── */
.input {
  background: var(--bg-base);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  padding: 8px 12px;
}
.input:focus {
  outline: none;
  border-color: var(--border-strong);
}
.input::placeholder {
  color: var(--text-tertiary);
}

/* ── Code / terminal surfaces ── */
.code-block {
  background: var(--mono-bg);         /* #141414 */
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  font-family: 'Fragment Mono', monospace;
  font-size: 13px;
  color: var(--mono-text);            /* #D4D4D4 */
  padding: 16px;
}

/* ── Status badges ── */
.badge-success { background: rgba(34, 197, 94, 0.1);  color: var(--success); border: 1px solid rgba(34, 197, 94, 0.2);  border-radius: 4px; padding: 2px 8px; font-family: 'Fragment Mono', monospace; font-size: 11px; }
.badge-error   { background: rgba(239, 68, 68, 0.1);  color: var(--error);   border: 1px solid rgba(239, 68, 68, 0.2);  border-radius: 4px; padding: 2px 8px; font-family: 'Fragment Mono', monospace; font-size: 11px; }
.badge-warn    { background: rgba(245, 158, 11, 0.1); color: var(--warn);    border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 4px; padding: 2px 8px; font-family: 'Fragment Mono', monospace; font-size: 11px; }
.badge-replay  { background: var(--bg-elevated);       color: var(--replay);  border: 1px solid var(--border-default);   border-radius: 4px; padding: 2px 8px; font-family: 'Fragment Mono', monospace; font-size: 11px; }

/* ── Dividers ── */
.divider { height: 1px; background: var(--border-subtle); border: none; }

/* ── Focus ring (accessibility) ── */
*:focus-visible { outline: 1px solid var(--border-strong); outline-offset: 2px; }
```

### 19.6 Logo & Brand Guidelines

- **Logo mark:** Concept A — capsule/pill shape with double left-pointing rewind triangles and cursor dot
- **Logo color on dark (`#0A0A0A`) backgrounds:** White pill (`#F5F5F5`), white triangles, white dot
- **Logo color on light (`#F5F5F5`) backgrounds:** Black pill (`#0A0A0A`), black triangles, black dot
- **Wordmark font:** `Inter` 600, lowercase `capsule` — replaces Oxanium
- **Wordmark color:** `#F5F5F5` on dark, `#0A0A0A` on light
- **No color version of the logo** — monochrome only, in all contexts
- **Brand assets location:** `packages/cloud-web/public/brand/`
- **Minimum size:** 24px height for the mark; 80px width for the full wordmark

### 19.7 What This Palette Does Not Allow

These are hard rules. The AI coding agent must never violate them:

- **No indigo, purple, cyan, or any color accent** on interactive elements — CTAs are white only
- **No gradient fills** on any background or button
- **No glow or shadow effects** except a single subtle `box-shadow: 0 1px 3px rgba(0,0,0,0.4)` for elevated surfaces
- **No Oxanium or Space Grotesk** anywhere in the codebase — these fonts are fully removed
- **No colored borders** — all borders are shades of grey from the token list above
- **Semantic colors (success, warn, error, replay) are for status indicators only** — never for CTAs, headings, or decorative elements

### 19.8 Accessibility

- WCAG 2.1 Level AA compliance required
- `--text-primary` (#F5F5F5) on `--bg-base` (#0A0A0A) = 18.1:1 contrast ratio ✓
- `--text-secondary` (#A0A0A0) on `--bg-base` (#0A0A0A) = 5.7:1 contrast ratio ✓
- `--text-tertiary` (#606060) on `--bg-base` (#0A0A0A) = 2.7:1 — **use only for decorative/non-essential text, never for required reading**
- All interactive elements keyboard-navigable
- Focus indicators use `--border-strong` (#3A3A3A) — visible against dark backgrounds
- `prefers-reduced-motion` respected
- Screen reader testing: NVDA (Windows) and VoiceOver (macOS)

## 20. Appendix: Reference Materials

### 20.1 Persistent Storage Convention for AI Coding Agents

Per user preference: all artifacts, logs, and intermediate work generated during the build process must be stored in the user's Documents folder under a dedicated `Capsule Code/` directory:

```
~/Documents/Capsule Code/
├── architecture-decisions/
│   └── ADR-001-replay-engine-language.md
├── implementation-logs/
│   ├── 2026-05-27-sdk-core-day-1.md
│   └── ...
├── design-iterations/
├── meeting-notes/
└── reference-materials/
```

### 20.2 Key External Dependencies (Pinned Versions for Reproducibility)

Document subject to change; use latest stable as of build start.

| Dependency | Version Constraint |
|------------|-------------------|
| Python | >= 3.11, < 3.13 |
| Node.js | >= 20.0.0, < 22.0.0 |
| Rust | >= 1.75.0 |
| PostgreSQL | >= 15.0 |
| Redis | >= 7.0 |
| Docker | >= 24.0 |

### 20.3 Glossary

- **Agent:** An autonomous program that uses LLMs to perform multi-step tasks
- **Capsule:** A single `.capsule` file containing one captured agent session
- **Cassette:** Stored API responses for offline deterministic replay
- **Determinism:** The property that the same inputs produce the same outputs
- **Event:** A single recorded action within a session (LLM call, tool call, memory op)
- **Replay:** Re-executing a captured session
- **Branching:** Replaying from a specific step with modifications
- **Session:** A single end-to-end agent execution
- **Snapshot:** A captured state of agent memory at a specific point
- **Workspace:** A team account that owns sessions and members

### 20.4 References

- Y Combinator W26 Batch Analysis (Extruct AI, BuildMVPFast, May 2026)
- MIT NANDA "The GenAI Divide: State of AI in Business 2025"
- Gartner Press Release on Agentic AI Cancellation Forecast (June 2025)
- Cleanlab "AI Agents in Production 2025"
- LangChain "State of Agent Engineering 2025"
- OpenAI + Amazon Stateful Runtime Partnership Announcement (Feb 2026)

### 20.5 Document Maintenance

This TRD is a living document. Updates must be made via PR to this file with the following process:

1. Propose change in a draft PR
2. Update the version number in the document header
3. Add a CHANGELOG entry at the top of the document
4. Require sign-off from the project owner before merging

### 20.6 Out-of-Scope for V1

The following features are explicitly out of scope for the initial 18-month build:

- Multi-language SDKs beyond Python (TypeScript SDK planned for Phase 4+)
- Mobile applications
- On-premise installation outside of Docker
- AI agent training data labeling
- Direct integration with model providers (Anthropic, OpenAI Console)
- Custom hardware appliances

### 20.7 Open Questions Requiring Human Decision

The AI coding agent should flag and request human input on:

1. Final company name and legal entity structure (India Pvt Ltd vs Delaware LLC) — decision pending
2. Logo direction: **RESOLVED — Concept A (Signal Pill).** SVG generation is a Sprint 1 deliverable per `Capsule_Logo_Brief_v1.0.md`.
3. Specific YC application timing — apply when MRR ≥ ₹8L, growing 15%+ MoM for 3 months, 1,000+ GitHub stars
4. Pricing tier names — current placeholders "Hobby", "Pro", "Business" are acceptable; change only if enterprise feedback suggests different naming
5. Final domain name selection (capsule.dev vs capsulehq.com vs others) — decision pending
6. Co-founder equity split between Founder 1 and Ojasvin Yadav — must be agreed and documented before company registration
7. Sprint 6 start coordination — API contracts from Sprint 5 should be stable before the web UI build begins

---

**End of Document**

For questions or clarifications during implementation, the AI coding agent should consult this document first. Where this document is silent or ambiguous, default to established best practices from the referenced sources and flag the question for human review.

*Document prepared in accordance with the Monochrome Premium design system (v1.5).*
*Storage location: `~/Documents/Capsule Code/TRD-v1.5.md`*
