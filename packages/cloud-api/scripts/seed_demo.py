#!/usr/bin/env python
"""Seed a realistic-looking demo account for YC reviewers.

Creates:
  - a user (demo@capsule.dev / capsule2024)
  - a workspace ("Demo Workspace")
  - 12 sessions across 3 agent personas, spread over the last 7 days,
    each with a real `.capsule` archive (uploaded to object storage —
    or local disk in dev) so the dashboard's step inspector works exactly
    like it would for a real capture.
  - Replay rows for a few of the successful sessions.

Idempotent: if demo@capsule.dev already exists, the script prints the
credentials and exits without touching the database. Pass --force to
delete the existing demo account (and its sessions/replays/.capsule
blobs) and recreate it from scratch instead.

Usage:
    DATABASE_URL_DIRECT=postgresql://user:pass@host:port/db \\
        .venv/Scripts/python.exe scripts/seed_demo.py [--force]

Object storage: uses the same STORAGE_ENDPOINT / STORAGE_BUCKET /
STORAGE_ACCESS_KEY / STORAGE_SECRET_KEY settings the API itself reads
(via capsule_cloud.config.get_settings()). When STORAGE_ENDPOINT is unset
the .capsule files are written to the local disk fallback
(<cwd>/data/storage/...), same as local dev.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import os
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import zstandard as zstd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ulid  # noqa: E402
from sqlalchemy import create_engine, delete, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from capsule_cloud.auth import hash_password  # noqa: E402
from capsule_cloud.models import (  # noqa: E402
    Session as CloudSession,
)
from capsule_cloud.models import (
    ApiKey,
    AuditLog,
    Replay,
    User,
    Workspace,
    WorkspaceMember,
)
from capsule_cloud import storage as _storage  # noqa: E402

DEMO_EMAIL = "demo@capsule.dev"
DEMO_PASSWORD = "capsule2024"
DEMO_NAME = "Demo User"
WORKSPACE_NAME = "Demo Workspace"
WORKSPACE_SLUG = "demo-workspace"
DASHBOARD_URL = "https://capsule-five-delta.vercel.app"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(ulid.new())


# ─────────────────────────────────────────────────────────────────
# Per-agent step templates. Each template is a list of event dicts in
# the exact shape the API's /events endpoint expects (mirrors
# packages/sdk/src/capsule_trace/core/models.py's Event/LLMCallPayload/
# ToolCallPayload/MemoryPayload). A trailing tool_call/llm_call with an
# "error" key (and no "result"/"response") is how a step reads as failed
# in the dashboard — same convention the real SDK uses.
# ─────────────────────────────────────────────────────────────────


def _llm_event(idx, provider, model, messages, content, prompt_tok, completion_tok, ms, error=None):
    return {
        "event_type": "llm_call",
        "step_index": idx,
        "duration_ms": ms,
        "payload": {
            "provider": provider,
            "model": model,
            "parameters": {"temperature": 0.7, "max_tokens": 1024},
            "messages": messages,
            "response": None if error else {
                "content": content,
                "tool_calls": [],
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": prompt_tok,
                    "completion_tokens": completion_tok,
                    "total_tokens": prompt_tok + completion_tok,
                },
            },
            "error": error,
        },
    }


def _tool_event(idx, tool_name, arguments, result=None, error=None, ms=200):
    return {
        "event_type": "tool_call",
        "step_index": idx,
        "duration_ms": ms,
        "payload": {
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "error": error,
        },
    }


def _stamp_events(session_id: str, started_at: datetime, events: list[dict]) -> list[dict]:
    """Fill in the fields the real Event schema requires that the builders
    above don't know about at construction time: event_id, session_id, and
    a realistic per-event timestamp (each event starts where the previous
    one's duration left off). parent_event_id is always None here — none of
    these synthetic events are nested/forked from another.

    Required because the SDK's replay engine (engine.py's _Archive.from_bytes)
    reads these via direct dict indexing — d["event_id"], d["session_id"],
    d["timestamp"] — not through lenient pydantic construction, so a missing
    key is a bare KeyError that aborts the whole replay ("capsule replay
    exited with code 1"), even though the dashboard's own /events reader
    (which only maps fields for display) doesn't care and shows the step
    fine. Confirmed by reproducing the failure directly against a seeded
    .capsule file before this fix.
    """
    cursor = started_at
    for ev in events:
        ev["event_id"] = _new_id()
        ev["session_id"] = session_id
        ev["parent_event_id"] = None
        ev["timestamp"] = cursor.isoformat()
        cursor = cursor + timedelta(milliseconds=ev["duration_ms"])
    return events


def _memory_event(idx, key, value, memory_type="scratchpad", ms=15):
    return {
        "event_type": "memory_write",
        "step_index": idx,
        "duration_ms": ms,
        "payload": {"memory_type": memory_type, "key": key, "value": value, "value_type": "json"},
    }


def customer_support_steps(customer_id, issue, outcome):
    steps = [
        _llm_event(
            0, "openai", "gpt-4o-mini",
            [
                {"role": "system", "content": "You are Acme's customer support agent. Resolve the ticket using the tools provided."},
                {"role": "user", "content": f"Customer {customer_id}: {issue}"},
            ],
            "Plan: look up the customer's account, check recent order history, then draft a reply.",
            312, 41, 640,
        ),
        _tool_event(
            1, "crm.lookup_customer", {"customer_id": customer_id},
            result={"customer_id": customer_id, "plan": "pro", "recent_orders": 3, "open_tickets": 1},
            ms=310,
        ),
        _memory_event(2, "ticket_context", {"customer_id": customer_id, "issue": issue}),
    ]
    if outcome == "failed":
        steps.append(_tool_event(
            3, "helpdesk.send_reply",
            {"customer_id": customer_id, "message": "Drafted reply pending send"},
            error="HelpdeskAPIError: connection timed out after 30s",
            ms=30_040,
        ))
        return steps
    steps.append(_llm_event(
        3, "openai", "gpt-4o-mini",
        [{"role": "user", "content": "Draft a reply resolving the issue."}],
        "Hi — thanks for reaching out. I've reviewed your account and resolved the issue. "
        "You'll see this reflected within a few minutes.",
        188, 52, 710,
    ))
    steps.append(_tool_event(
        4, "helpdesk.send_reply",
        {"customer_id": customer_id, "message": "reply sent"},
        result={"status": "sent", "ticket_status": "resolved"},
        ms=180,
    ))
    return steps


def research_steps(topic, outcome):
    steps = [
        _llm_event(
            0, "openai", "gpt-4o",
            [
                {"role": "system", "content": "You are a research agent. Investigate the topic thoroughly before answering."},
                {"role": "user", "content": topic},
            ],
            "Plan: search for primary sources, extract key facts, synthesize a cited answer.",
            268, 47, 590,
        ),
    ]
    if outcome == "failed":
        steps.append(_tool_event(
            1, "web.search", {"query": topic},
            error="SearchAPIError: rate limit exceeded (429) — retry after 60s",
            ms=210,
        ))
        return steps
    if outcome == "cancelled":
        steps.append(_tool_event(
            1, "web.search", {"query": topic},
            result={"results": 6, "top_source": "arxiv.org"},
            ms=480,
        ))
        return steps
    steps.append(_tool_event(
        1, "web.search", {"query": topic},
        result={"results": 8, "top_source": "arxiv.org"},
        ms=520,
    ))
    steps.append(_memory_event(2, "rag_context", {"topic": topic, "sources": 8}, memory_type="rag_context"))
    steps.append(_llm_event(
        3, "openai", "gpt-4o",
        [{"role": "user", "content": "Synthesize the findings into a final answer with citations."}],
        f"Summary of findings on '{topic}', synthesized from 8 sources with inline citations.",
        1_204, 386, 1_850,
    ))
    return steps


def data_pipeline_steps(source, outcome):
    steps = [
        _tool_event(0, "pipeline.extract", {"source": source}, result={"rows_extracted": 48_213}, ms=4_200),
        _tool_event(1, "pipeline.transform", {"schema": "v2"}, result={"rows_transformed": 48_213}, ms=2_800),
    ]
    if outcome == "failed":
        steps.append(_tool_event(
            2, "pipeline.load", {"destination": "warehouse.events"},
            error='warehouse.load: constraint violation — duplicate key value violates unique constraint "events_pkey"',
            ms=1_100,
        ))
        return steps
    steps.append(_tool_event(2, "pipeline.load", {"destination": "warehouse.events"}, result={"rows_loaded": 48_213}, ms=3_100))
    steps.append(_llm_event(
        3, "openai", "gpt-4o-mini",
        [{"role": "user", "content": "Validate the pipeline run and summarize."}],
        "Pipeline run completed: 48,213 rows processed, 0 anomalies detected.",
        142, 28, 480,
    ))
    return steps


# ─────────────────────────────────────────────────────────────────
# Session plan: (agent_name, agent_version, outcome, hours_ago, builder, args)
# 12 sessions total — 8 success, 3 failed, 1 cancelled, spread over 7 days.
# ─────────────────────────────────────────────────────────────────

SESSION_PLAN = [
    ("customer-support-agent", "2.3.0", "success", 3, customer_support_steps, ("cus_8K2M1P", "duplicate charge on last invoice")),
    ("customer-support-agent", "2.3.0", "success", 9, customer_support_steps, ("cus_4NQXW2", "shipping address needs updating")),
    ("customer-support-agent", "2.3.0", "success", 22, customer_support_steps, ("cus_7RT903", "can't access premium features")),
    ("customer-support-agent", "2.3.0", "failed", 30, customer_support_steps, ("cus_2VXQ88", "refund request stuck in processing")),
    ("customer-support-agent", "2.2.1", "success", 46, customer_support_steps, ("cus_9PLK04", "question about billing cycle")),
    ("customer-support-agent", "2.2.1", "success", 71, customer_support_steps, ("cus_1MZT56", "wants to downgrade plan")),
    ("research-agent", "1.4.0", "success", 14, research_steps, ("competitive landscape for AI observability tools",)),
    ("research-agent", "1.4.0", "cancelled", 27, research_steps, ("EU AI Act compliance requirements for logging",)),
    ("research-agent", "1.4.0", "failed", 55, research_steps, ("latest benchmarks for long-context LLM retrieval",)),
    ("research-agent", "1.3.2", "success", 98, research_steps, ("pricing models used by developer-tool startups",)),
    ("data-pipeline-agent", "3.1.0", "success", 63, data_pipeline_steps, ("postgres_replica",)),
    ("data-pipeline-agent", "3.1.0", "failed", 118, data_pipeline_steps, ("postgres_replica",)),
]

# Indices (into SESSION_PLAN) of successful sessions that also get a
# completed, deterministic Replay row.
REPLAYED_INDICES = [0, 2, 6]


def _capsule_bytes(session_id: str, meta: dict, events: list[dict]) -> bytes:
    """Build a zstd-compressed tar matching the real .capsule format
    (events/NNNN-<type>.json, session.json, manifest.json)."""
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        event_blobs: list[bytes] = []
        for idx, ev in enumerate(events):
            filename = f"events/{idx + 1:04d}-{ev['event_type']}.json"
            blob = json.dumps(ev, indent=2, default=str).encode("utf-8")
            event_blobs.append(blob)
            _add_bytes(tar, filename, blob)

        session_blob = json.dumps(meta, indent=2, default=str).encode("utf-8")
        _add_bytes(tar, "session.json", session_blob)

        manifest = {
            "capsule_version": "1.0",
            "format_spec_url": "https://capsule-five-delta.vercel.app/spec/v1.0",
            "created_at": _now().isoformat(),
            "session_id": session_id,
            "integrity": {
                "algorithm": "sha256",
                "events_hash": hashlib.sha256(b"".join(event_blobs)).hexdigest(),
                "cassettes_hash": hashlib.sha256(b"").hexdigest(),
                "snapshots_hash": hashlib.sha256(b"").hexdigest(),
            },
            "encryption": {"enabled": False},
            "compression": {"algorithm": "zstd", "level": 3},
            "producer": {
                "sdk_name": "capsule-python",
                "sdk_version": "0.1.2",
                "platform": "x86_64",
                "python_version": "3.11.9",
            },
        }
        _add_bytes(tar, "manifest.json", json.dumps(manifest, indent=2).encode("utf-8"))

    raw_tar = tar_buffer.getvalue()
    cctx = zstd.ZstdCompressor(level=3)
    return cctx.compress(raw_tar)


def _add_bytes(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def _cost_for(steps: list[dict]) -> tuple[int, int, float]:
    in_tok = out_tok = 0
    cost = 0.0
    for ev in steps:
        if ev["event_type"] != "llm_call" or not ev["payload"].get("response"):
            continue
        usage = ev["payload"]["response"]["usage"]
        in_tok += usage["prompt_tokens"]
        out_tok += usage["completion_tokens"]
        # rough blended per-1k-token rate, just for a plausible dollar figure
        cost += usage["prompt_tokens"] / 1000 * 0.0025 + usage["completion_tokens"] / 1000 * 0.01
    return in_tok, out_tok, round(cost, 6)


def _teardown_existing(db, existing_user: User) -> None:
    """Delete the demo user and everything scoped to their workspace(s) —
    replays, sessions (DB rows + their object-storage .capsule blobs),
    api keys, audit logs, memberships, and the workspace(s) themselves — so
    --force gives a genuinely clean slate rather than erroring on
    unique-constraint conflicts (e.g. the workspace slug) if creation runs
    again.

    Every child table with a workspace_id FK is deleted explicitly here,
    rather than relying on the DB's ON DELETE CASCADE or SQLAlchemy's ORM
    cascade: Workspace.api_keys is a declared relationship without
    passive_deletes, so the ORM's default behaviour on `db.delete(ws)` is to
    try to *null out* each ApiKey's workspace_id instead of deleting the
    row — which fails outright since that column is NOT NULL. Explicit
    deletes sidestep that regardless of how any given relationship is
    configured.
    """
    workspaces = db.execute(
        select(Workspace).where(Workspace.owner_id == existing_user.id)
    ).scalars().all()

    for ws in workspaces:
        sessions = db.execute(
            select(CloudSession).where(CloudSession.workspace_id == ws.id)
        ).scalars().all()

        for s in sessions:
            try:
                asyncio.run(_storage.delete(s.storage_path))
            except Exception as exc:  # best-effort — a missing/already-gone blob shouldn't block teardown
                print(f"  (warning: could not delete storage blob {s.storage_path}: {exc})", file=sys.stderr)

        db.execute(delete(Replay).where(Replay.workspace_id == ws.id))
        db.execute(delete(CloudSession).where(CloudSession.workspace_id == ws.id))
        db.execute(delete(ApiKey).where(ApiKey.workspace_id == ws.id))
        db.execute(delete(AuditLog).where(AuditLog.workspace_id == ws.id))
        db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == ws.id))
        db.delete(ws)

    db.delete(existing_user)
    db.commit()
    print(f"Tore down existing '{DEMO_EMAIL}' account: {len(workspaces)} workspace(s) and their sessions/replays removed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the existing demo account (user, workspace, sessions, replays, "
             "and their .capsule blobs in object storage) and recreate it from scratch, "
             "instead of no-op'ing when demo@capsule.dev already exists.",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: set DATABASE_URL_DIRECT (or DATABASE_URL) to a plain postgresql:// URL.", file=sys.stderr)
        sys.exit(1)

    # Fail fast, loudly, and before touching the database: if real object
    # storage is configured (i.e. this is pointed at production, not the
    # local-disk fallback), every session upload below needs aiobotocore.
    # Without this check, a missing dependency only shows up as repeated
    # "could not delete storage blob" warnings during teardown (delete()
    # degrades gracefully) followed by a hard crash on the very first
    # session's upload() a moment later (which does not, and should not,
    # degrade gracefully — a "successful" seed with no real .capsule data
    # would silently reintroduce the broken-replay bug this script exists
    # to fix).
    from capsule_cloud.config import get_settings
    settings = get_settings()
    if settings.storage_endpoint:
        try:
            import aiobotocore.session  # noqa: F401
        except ImportError:
            print(
                "ERROR: STORAGE_ENDPOINT is configured (this DB points at production), "
                "which means uploading .capsule files needs aiobotocore, but it isn't "
                "installed in this Python environment.\n"
                "Fix: pip install \"aiobotocore[boto3]>=2.13.0\"\n"
                "  (or: pip install -r " + str(Path(__file__).resolve().parent.parent / "requirements.txt") + ")",
                file=sys.stderr,
            )
            sys.exit(1)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    # This is a sync script (psycopg2) — strip any async driver suffix if present.
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(database_url, future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)

    def _print_creds():
        print("\nDemo account ready:")
        print(f"  Email:     {DEMO_EMAIL}")
        print(f"  Password:  {DEMO_PASSWORD}")
        print(f"  Dashboard: {DASHBOARD_URL}")

    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == DEMO_EMAIL)).scalars().first()
        if existing is not None:
            if not args.force:
                print(f"'{DEMO_EMAIL}' already exists — skipping seed (idempotent no-op). Use --force to recreate.")
                _print_creds()
                return
            _teardown_existing(db, existing)

        user_id = _new_id()
        user = User(
            id=user_id,
            email=DEMO_EMAIL,
            full_name=DEMO_NAME,
            hashed_password=hash_password(DEMO_PASSWORD),
            auth_provider="email",
        )
        db.add(user)

        ws_id = _new_id()
        workspace = Workspace(
            id=ws_id,
            name=WORKSPACE_NAME,
            slug=WORKSPACE_SLUG,
            owner_id=user_id,
            plan_tier="pro",
        )
        db.add(workspace)

        db.add(WorkspaceMember(id=_new_id(), workspace_id=ws_id, user_id=user_id, role="owner"))
        db.flush()

        total_storage_bytes = 0
        created_sessions: list[tuple[str, str, int]] = []  # (session_id, outcome, step_count)

        for plan_idx, (agent_name, agent_version, outcome, hours_ago, builder, args) in enumerate(SESSION_PLAN):
            session_id = _new_id()
            started_at = _now() - timedelta(hours=hours_ago)

            steps = builder(*args, outcome)
            steps = _stamp_events(session_id, started_at, steps)
            step_count = len(steps)
            duration_ms = sum(ev["duration_ms"] for ev in steps)
            ended_at = started_at + timedelta(milliseconds=duration_ms)
            in_tok, out_tok, cost = _cost_for(steps)

            status = {"success": "success", "failed": "failed", "cancelled": "cancelled"}[outcome]
            error_type = error_message = None
            if outcome == "failed":
                last = steps[-1]["payload"]
                error_message = last.get("error")
                error_type = (
                    "HelpdeskAPIError" if "Helpdesk" in (error_message or "") else
                    "SearchAPIError" if "SearchAPI" in (error_message or "") else
                    "PipelineLoadError"
                )

            session_meta = {
                "session_id": session_id,
                "agent_name": agent_name,
                "agent_version": agent_version,
                "started_at": started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
                "duration_ms": duration_ms,
                "status": status,
                "error": {"type": error_type, "message": error_message} if error_type else None,
                "tags": ["demo"],
                "user_metadata": {},
                "step_count": step_count,
                "total_tokens": {"input": in_tok, "output": out_tok},
                "total_cost_usd": cost,
            }

            capsule_bytes = _capsule_bytes(session_id, session_meta, steps)
            storage_path = f"{ws_id}/{session_id}.capsule"
            asyncio.run(_storage.upload(storage_path, capsule_bytes))
            total_storage_bytes += len(capsule_bytes)

            db.add(CloudSession(
                id=session_id,
                workspace_id=ws_id,
                agent_name=agent_name,
                agent_version=agent_version,
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=int(duration_ms),
                status=status,
                step_count=step_count,
                total_input_tokens=in_tok,
                total_output_tokens=out_tok,
                total_cost_usd=cost,
                error_type=error_type,
                error_message=error_message,
                tags_json=json.dumps(["demo"]),
                user_metadata_json="{}",
                storage_path=storage_path,
                storage_size_bytes=len(capsule_bytes),
                integrity_hash=hashlib.sha256(capsule_bytes).hexdigest(),
                capsule_format_version="1.0",
                uploaded_by_id=user_id,
                uploaded_at=started_at,
                expires_at=_now() + timedelta(days=90),
            ))
            created_sessions.append((session_id, outcome, step_count))

        workspace.storage_used_bytes = total_storage_bytes

        # Force all CloudSession rows to be physically inserted before the
        # Replay rows are added — Postgres (unlike SQLite's default config)
        # enforces the replays_session_id_fkey constraint at insert time, and
        # without this explicit boundary the two batches can be sequenced
        # such that a replay row's session_id isn't visible yet.
        db.flush()

        for idx in REPLAYED_INDICES:
            session_id, outcome, step_count = created_sessions[idx]
            assert outcome == "success", "REPLAYED_INDICES must point at successful sessions"
            db.add(Replay(
                id=_new_id(),
                session_id=session_id,
                workspace_id=ws_id,
                mode="cassette",
                status="completed",
                result_json=json.dumps({
                    "is_deterministic": True,
                    "integrity_ok": True,
                    "replayed_steps": step_count,
                    "original_steps": step_count,
                }),
                created_by_id=user_id,
            ))

        db.commit()

    print(f"Created user, workspace, {len(SESSION_PLAN)} sessions, {len(REPLAYED_INDICES)} replays.")
    _print_creds()


if __name__ == "__main__":
    main()
