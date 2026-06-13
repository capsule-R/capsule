# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
End-to-end test: build a .capsule file with status=failed and verify it.

Steps
-----
1. Build the .capsule archive (zstd-compressed tar) with 2 events
2. Start the local API server (uvicorn) in a subprocess
3. Sign up a fresh test user  (auto-creates a workspace)
4. List workspaces → capture workspace_id
5. Upload the .capsule file via multipart POST
6. Verify:
   (a) GET session       → status=="failed", step_count==2
   (b) GET events        → returns 2 events, never 500
   (c) Check what the dashboard badge would show
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
import zstandard

import httpx

# ── Config ────────────────────────────────────────────────────────────────────

API_BASE   = "http://localhost:8000/api/v1"
import time as _time
SESSION_ID = f"ses-billing-failed-{int(_time.time())}"
TEST_EMAIL = "capsule-e2e@example.com"
TEST_PASS  = "E2eTestPass99!"

# ── Step 1: Build the .capsule archive ───────────────────────────────────────

def build_capsule() -> bytes:
    """Construct a valid minimal .capsule file entirely in memory."""

    start_ts = "2026-06-13T10:00:00.000Z"
    end_ts   = "2026-06-13T10:01:23.456Z"

    event1_data = {
        "event_id":        "evt_0001",
        "session_id":      SESSION_ID,
        "step_index":      1,
        "parent_event_id": None,
        "event_type":      "llm_call",
        "timestamp":       "2026-06-13T10:00:05.100Z",
        "duration_ms":     1240,
        "payload": {
            "provider": "openai",
            "model":    "gpt-4o",
            "parameters": {"temperature": 0.7, "max_tokens": 512},
            "messages": [
                {"role": "system",  "content": "You are a billing assistant."},
                {"role": "user",    "content": "Process a refund for order ORD-9999"},
            ],
            "response": {
                "content":       "I will process that refund right away.",
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens":     120,
                    "completion_tokens":  45,
                    "total_tokens":      165,
                },
            },
        },
    }

    event2_data = {
        "event_id":        "evt_0002",
        "session_id":      SESSION_ID,
        "step_index":      2,
        "parent_event_id": "evt_0001",
        "event_type":      "error",
        "timestamp":       "2026-06-13T10:01:23.400Z",
        "duration_ms":     0,
        "payload": {
            "error_type":    "ToolExecutionError",
            "error_message": "Refund amount $1500 exceeds policy limit of $500",
            "stack_trace":   (
                "Traceback (most recent call last):\n"
                "  File 'billing_agent.py', line 42, in execute_refund\n"
                "    raise PolicyViolation('Refund amount exceeds limit')\n"
                "PolicyViolation: Refund amount $1500 exceeds policy limit of $500"
            ),
            "is_fatal": True,
        },
    }

    e1_bytes = json.dumps(event1_data, indent=2).encode()
    e2_bytes = json.dumps(event2_data, indent=2).encode()

    # Integrity: SHA-256 of concatenated event files in filename-sorted order
    events_hash = hashlib.sha256(e1_bytes + e2_bytes).hexdigest()

    session_json = {
        "session_id":  SESSION_ID,
        "agent_name":  "billing-agent-v3",
        "agent_version": "3.2.1",
        "started_at":  start_ts,
        "ended_at":    end_ts,
        "duration_ms": 83456,
        "status":      "failed",
        "error": {
            "type":    "ToolExecutionError",
            "message": "Refund amount $1500 exceeds policy limit of $500",
        },
        "tags":        ["refund", "production", "failed"],
        "step_count":  2,
        "total_tokens": {"input": 120, "output": 45},
        "total_cost_usd": 0.00165,
    }

    manifest = {
        "capsule_version":  "1.0",
        "format_spec_url":  "https://capsule.dev/spec/v1.0",
        "created_at":       start_ts,
        "session_id":       SESSION_ID,
        "integrity": {
            "algorithm":       "sha256",
            "events_hash":     events_hash,
            "cassettes_hash":  hashlib.sha256(b"").hexdigest(),
            "snapshots_hash":  hashlib.sha256(b"").hexdigest(),
        },
        "encryption":  {"enabled": False, "algorithm": None, "key_hint": None},
        "compression": {"algorithm": "zstd", "level": 3},
        "producer": {
            "sdk_name":       "capsule-python",
            "sdk_version":    "0.1.0",
            "platform":       "win32-x86_64",
            "python_version": "3.13.7",
        },
    }

    # Assemble tar in memory
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        def _add(name: str, data: bytes) -> None:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        _add("manifest.json",           json.dumps(manifest,      indent=2).encode())
        _add("session.json",            json.dumps(session_json,  indent=2).encode())
        _add("events/0001-llm_call.json", e1_bytes)
        _add("events/0002-error.json",    e2_bytes)

    # Compress
    return zstandard.ZstdCompressor(level=3).compress(tar_buf.getvalue())


# ── Step 2: Server lifecycle ──────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    """Launch uvicorn in the background, reading .env from the project root."""
    env = os.environ.copy()
    # Force local-disk storage fallback — avoids needing aiobotocore installed
    env["STORAGE_ENDPOINT"] = ""
    env["STORAGE_ACCESS_KEY"] = ""
    env["STORAGE_SECRET_KEY"] = ""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "capsule_cloud.main:app",
         "--host", "127.0.0.1",
         "--port", "8000",
         "--log-level", "warning"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # repo root
        env=env,
    )
    return proc


def wait_for_server(timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get("http://localhost:8000/api/v1/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# ── Step 3-6: API interactions ────────────────────────────────────────────────

def run_test(capsule_bytes: bytes) -> None:
    client = httpx.Client(base_url=API_BASE, timeout=30)

    # ── Signup ────────────────────────────────────────────────
    print("\n[1/6] Signing up test user …")
    r = client.post("/auth/signup", json={
        "email":     TEST_EMAIL,
        "password":  TEST_PASS,
        "full_name": "E2E Test",
    })
    if r.status_code == 409:
        # Already exists — just log in
        r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS})
    if not r.is_success:
        print(f"    ERROR [{r.status_code}]: {r.text}")
        r.raise_for_status()
    tokens = r.json()
    access_token = tokens["access_token"]
    auth = {"Authorization": f"Bearer {access_token}"}
    print(f"    ✓ authenticated (token starts with {access_token[:20]}…)")

    # ── Workspace ─────────────────────────────────────────────
    print("\n[2/6] Getting workspace ID …")
    r = client.get("/workspaces", headers=auth)
    r.raise_for_status()
    workspaces = r.json()
    workspace_id = workspaces[0]["id"]
    print(f"    ✓ workspace_id = {workspace_id}")

    # ── Delete prior run if it exists ────────────────────────
    prior = client.delete(
        f"/workspaces/{workspace_id}/sessions/{SESSION_ID}", headers=auth,
    )
    if prior.status_code == 204:
        print("\n    (deleted prior session from last run)")

    # ── Upload ────────────────────────────────────────────────
    print("\n[3/6] Uploading .capsule file …")
    upload_meta = json.dumps({
        "session_id":  SESSION_ID,
        "agent_name":  "billing-agent-v3",
        "agent_version": "3.2.1",
        "tags":        ["refund", "production", "failed"],
        "user_metadata": {},
        "auto_redact": False,
    })
    r = client.post(
        f"/workspaces/{workspace_id}/sessions",
        headers=auth,
        files={
            "file":     ("billing-failed.capsule", capsule_bytes, "application/octet-stream"),
            "metadata": (None, upload_meta, "application/json"),
        },
        # Note: don't set Content-Type here — httpx sets multipart boundary automatically
    )
    if r.status_code not in (200, 201):
        print(f"    ✗ Upload failed [{r.status_code}]: {r.text}")
        return
    session = r.json()
    print(f"    ✓ uploaded: status={session['status']}  step_count={session['step_count']}")

    # ── Verify (a): GET session ───────────────────────────────
    print("\n[4/6] GET session — checking status and step_count …")
    r = client.get(f"/workspaces/{workspace_id}/sessions/{SESSION_ID}", headers=auth)
    r.raise_for_status()
    s = r.json()

    status_ok     = s["status"] == "failed"
    step_count_ok = s["step_count"] == 2

    print(f"    status     = {s['status']!r}  {'✓' if status_ok else '✗ EXPECTED failed'}")
    print(f"    step_count = {s['step_count']}  {'✓' if step_count_ok else '✗ EXPECTED 2'}")
    print(f"    error_type = {s.get('error_type')!r}")
    print(f"    error_msg  = {s.get('error_message')!r}")

    # ── Verify (b): GET events ────────────────────────────────
    print("\n[5/6] GET /events — non-negotiable: must return 200 with 2 events …")
    r = client.get(f"/workspaces/{workspace_id}/sessions/{SESSION_ID}/events", headers=auth)
    events_status_ok = r.status_code == 200
    events = r.json() if events_status_ok else []
    events_count_ok  = len(events) == 2

    print(f"    HTTP {r.status_code}  {'✓' if events_status_ok else '✗ EXPECTED 200'}")
    print(f"    events returned = {len(events)}  {'✓' if events_count_ok else '✗ EXPECTED 2'}")
    if events:
        for i, ev in enumerate(events, 1):
            print(f"      [{i}] step_index={ev.get('step_index')}  "
                  f"event_type={ev.get('event_type')!r}  "
                  f"event_id={ev.get('event_id')!r}")

    # ── Dashboard badge ───────────────────────────────────────
    print("\n[6/6] Dashboard representation …")
    badge_color = "red" if s["status"] == "failed" else "grey"
    print(f"    Session ID  : {s['id']}")
    print(f"    Agent       : {s['agent_name']}  v{s.get('agent_version', '?')}")
    print(f"    Badge       : [{badge_color.upper()}] {s['status'].upper()}")
    print(f"    Steps       : {s['step_count']}")
    print(f"    Duration    : {s.get('duration_ms', '?')} ms")
    print(f"    Cost        : ${s.get('total_cost_usd', 0):.5f}")
    print(f"    Error       : {s.get('error_type')} — {s.get('error_message')}")

    all_pass = status_ok and step_count_ok and events_status_ok and events_count_ok
    print(f"\n{'='*55}")
    print(f"  RESULT: {'ALL CHECKS PASSED ✓' if all_pass else 'SOME CHECKS FAILED ✗'}")
    print(f"{'='*55}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 55)
    print("  Capsule end-to-end: failed session upload + verify")
    print("=" * 55)

    # Build archive first (no server needed)
    print("\n[0/6] Building .capsule archive …")
    capsule_bytes = build_capsule()
    print(f"    ✓ archive ready ({len(capsule_bytes):,} bytes)")

    # Local round-trip verification before touching the server
    print("\n[0b/6] Verifying archive locally …")
    import zstandard as _zstd
    dctx = _zstd.ZstdDecompressor()
    raw_tar = dctx.decompress(capsule_bytes)
    import tarfile as _tarfile
    with _tarfile.open(fileobj=io.BytesIO(raw_tar)) as t:
        members = [m.name for m in t.getmembers()]
        print(f"    TAR members: {members}")
        # Verify session.json
        f = t.extractfile("session.json")
        sj = json.loads(f.read())
        print(f"    session.json status={sj['status']!r}  step_count={sj['step_count']}")
        # Verify events
        evts = [m for m in members if m.startswith("events/")]
        print(f"    events: {evts}")
    print("    ✓ archive round-trips correctly")

    # Check if server is already up; start it if not
    server_proc = None
    try:
        r = httpx.get("http://localhost:8000/api/v1/health", timeout=2)
        print("\n    Using already-running API server on :8000")
    except Exception:
        print("\n    Starting local API server on :8000 …")
        server_proc = start_server()
        if not wait_for_server():
            print("    ✗ Server did not start within 30s")
            server_proc.terminate()
            sys.exit(1)
        print("    ✓ Server is up")

    try:
        run_test(capsule_bytes)
    finally:
        if server_proc:
            server_proc.terminate()
            print("    Server stopped.")


if __name__ == "__main__":
    main()
