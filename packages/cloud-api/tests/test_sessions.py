"""Tests for session upload, list, get, delete, events, replay, and branch endpoints."""

from __future__ import annotations

import io
import json
import tarfile
import uuid

import zstandard as zstd


def _make_capsule_bytes(session_id: str | None = None) -> bytes:
    """Build a minimal valid .capsule archive for testing."""
    sid = session_id or str(uuid.uuid4())
    session_data = {
        "session_id": sid,
        "agent_name": "test-agent",
        "status": "completed",
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:01:00+00:00",
        "duration_ms": 60000,
        "step_count": 3,
    }

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        session_bytes = json.dumps(session_data).encode()
        info = tarfile.TarInfo(name="session.json")
        info.size = len(session_bytes)
        tar.addfile(info, io.BytesIO(session_bytes))

    raw_tar = tar_buf.getvalue()
    cctx = zstd.ZstdCompressor()
    return cctx.compress(raw_tar)


def _make_capsule_with_events(session_id: str, events: list) -> bytes:
    """Build a .capsule archive with events/ directory entries."""
    session_data = {
        "session_id": session_id,
        "agent_name": "test-agent",
        "status": "completed",
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:01:00+00:00",
        "duration_ms": 60000,
        "step_count": len(events),
    }
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        b = json.dumps(session_data).encode()
        info = tarfile.TarInfo(name="session.json")
        info.size = len(b)
        tar.addfile(info, io.BytesIO(b))
        for i, event in enumerate(events):
            eb = json.dumps(event).encode()
            einfo = tarfile.TarInfo(name=f"events/{i:04d}-event.json")
            einfo.size = len(eb)
            tar.addfile(einfo, io.BytesIO(eb))
    return zstd.ZstdCompressor().compress(tar_buf.getvalue())


def _make_capsule_with_usage(
    session_id: str,
    *,
    cost: float = 0.0,
    in_tok: int = 0,
    out_tok: int = 0,
    status: str = "success",
    error: dict | None = None,
) -> bytes:
    session_data: dict = {
        "session_id": session_id,
        "agent_name": "test-agent",
        "status": status,
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:01:00+00:00",
        "duration_ms": 60000,
        "step_count": 3,
        "total_cost_usd": cost,
        "total_tokens": {"input": in_tok, "output": out_tok},
    }
    if error is not None:
        session_data["error"] = error

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        b = json.dumps(session_data).encode()
        info = tarfile.TarInfo(name="session.json")
        info.size = len(b)
        tar.addfile(info, io.BytesIO(b))
    return zstd.ZstdCompressor().compress(tar_buf.getvalue())


async def _upload_session(client, workspace_id, auth_headers, session_id=None):
    sid = session_id or str(uuid.uuid4())
    capsule_bytes = _make_capsule_bytes(sid)
    metadata = json.dumps(
        {
            "session_id": sid,
            "agent_name": "test-agent",
            "agent_version": "1.0.0",
            "tags": ["test"],
            "user_metadata": {},
            "auto_redact": False,
        }
    )
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
        data={"metadata": metadata},
        headers=auth_headers,
    )


async def _upload_capsule(client, workspace_id, auth_headers, sid, capsule_bytes):
    metadata = json.dumps(
        {"session_id": sid, "agent_name": "test-agent", "agent_version": "1.0.0",
         "tags": [], "user_metadata": {}, "auto_redact": False}
    )
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
        data={"metadata": metadata},
        headers=auth_headers,
    )


async def _upload_with_agent(client, workspace_id, auth_headers, sid, agent_name="test-agent"):
    """Upload a minimal .capsule with a custom agent_name."""
    capsule_bytes = _make_capsule_bytes(sid)
    metadata = json.dumps({
        "session_id": sid,
        "agent_name": agent_name,
        "agent_version": "1.0.0",
        "tags": [],
        "user_metadata": {},
        "auto_redact": False,
    })
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
        data={"metadata": metadata},
        headers=auth_headers,
    )


class TestSessionUpload:
    async def test_upload_success(self, client, auth_headers, workspace_id):
        resp = await _upload_session(client, workspace_id, auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["workspace_id"] == workspace_id
        assert data["agent_name"] == "test-agent"
        assert data["status"] == "completed"
        assert data["tags"] == ["test"]

    async def test_upload_duplicate_session_id(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        resp1 = await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        assert resp1.status_code == 201
        resp2 = await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        assert resp2.status_code == 409

    async def test_upload_invalid_metadata_json(self, client, auth_headers, workspace_id):
        capsule_bytes = _make_capsule_bytes()
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
            data={"metadata": "this is not json"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_upload_unauthenticated(self, client, workspace_id):
        capsule_bytes = _make_capsule_bytes()
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
            data={"metadata": "{}"},
        )
        assert resp.status_code == 401


class TestSessionList:
    async def test_list_empty(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "List Test", "slug": "list-test-ws-2"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        ws_id = resp.json()["id"]
        resp = await client.get(
            f"/api/v1/workspaces/{ws_id}/sessions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_after_upload(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [s["id"] for s in data["items"]]
        assert sid in ids


class TestSessionGet:
    async def test_get_existing_session(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    async def test_get_nonexistent_session(self, client, auth_headers, workspace_id):
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/does-not-exist",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestSessionDelete:
    async def test_delete_session(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
        resp2 = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp2.status_code == 404


class TestCostTokenExtraction:
    async def test_cost_and_tokens_extracted(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_usage(sid, cost=0.0171, in_tok=1200, out_tok=340)
        resp = await _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert abs(data["total_cost_usd"] - 0.0171) < 1e-6
        assert data["total_input_tokens"] == 1200
        assert data["total_output_tokens"] == 340

    async def test_nested_error_extracted(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_usage(
            sid, status="failed", error={"type": "ValueError", "message": "boom"}
        )
        resp = await _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error_type"] == "ValueError"
        assert data["error_message"] == "boom"


class TestSessionStats:
    async def test_stats_empty(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "Stats WS", "slug": "stats-ws-empty"},
            headers=auth_headers,
        )
        ws_id = resp.json()["id"]
        resp = await client.get(
            f"/api/v1/workspaces/{ws_id}/sessions/stats", headers=auth_headers
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["total"] == 0
        assert data["failed"] == 0
        assert data["total_cost_usd"] == 0
        assert data["range_days"] == 30
        assert len(data["daily"]) == 30
        assert all(d["count"] == 0 for d in data["daily"])

    async def test_stats_after_uploads(self, client, auth_headers, workspace_id):
        ok = str(uuid.uuid4())
        bad = str(uuid.uuid4())
        await _upload_capsule(client, workspace_id, auth_headers, ok,
                              _make_capsule_with_usage(ok, cost=0.10, in_tok=10, out_tok=5))
        await _upload_capsule(client, workspace_id, auth_headers, bad,
                              _make_capsule_with_usage(bad, status="failed",
                                                       error={"type": "E", "message": "m"}))
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/stats?days=7",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["total"] == 2
        assert data["failed"] == 1
        assert abs(data["total_cost_usd"] - 0.10) < 1e-6
        assert data["range_days"] == 7
        assert len(data["daily"]) == 7
        assert sum(d["count"] for d in data["daily"]) == 2

    async def test_stats_route_not_shadowed_by_session_id(self, client, auth_headers, workspace_id):
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/stats", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "daily" in resp.json()


class TestSessionDownload:
    async def test_download_capsule(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/download",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert sid in resp.headers.get("content-disposition", "")
        tar_bytes = zstd.ZstdDecompressor().decompress(resp.content)
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
            names = tar.getnames()
        assert any(n.endswith("session.json") for n in names)

    async def test_download_nonexistent(self, client, auth_headers, workspace_id):
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/nope/download",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestSessionEvents:
    async def test_events_empty(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/events",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_events_with_data(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        events = [{"type": "tool_call", "step": 0}, {"type": "llm_response", "step": 1}]
        capsule_bytes = _make_capsule_with_events(sid, events)
        metadata = json.dumps({
            "session_id": sid, "agent_name": "test-agent", "agent_version": "1.0.0",
            "tags": [], "user_metadata": {}, "auto_redact": False,
        })
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
            data={"metadata": metadata},
            headers=auth_headers,
        )
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/events",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["type"] == "tool_call"
        assert data[1]["type"] == "llm_response"

    async def test_events_nonexistent_session(self, client, auth_headers, workspace_id):
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/no-such-session/events",
            headers=auth_headers,
        )
        assert resp.status_code == 404


def _make_capsule_with_steps(session_id: str, step_count: int) -> bytes:
    """Build a .capsule archive with a custom step_count."""
    session_data = {
        "session_id": session_id,
        "agent_name": "test-agent",
        "status": "completed",
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:01:00+00:00",
        "duration_ms": 60000,
        "step_count": step_count,
    }
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        b = json.dumps(session_data).encode()
        info = tarfile.TarInfo(name="session.json")
        info.size = len(b)
        tar.addfile(info, io.BytesIO(b))
    return zstd.ZstdCompressor().compress(tar_buf.getvalue())


class TestSessionReplay:
    async def test_replay_accepted(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["session_id"] == sid
        assert data["status"] in ("queued", "completed", "error")

    async def test_replay_nonexistent_session(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/no-such/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_replay_large_session_returns_error(self, client, auth_headers, workspace_id):
        """Sessions with >=30 steps cannot be replayed locally without Modal."""
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_steps(sid, step_count=35)
        await _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "error"
        assert data["session_id"] == sid


class TestSessionBranch:
    async def test_branch_create(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        # session has step_count=3; from_step=0 is valid (0 < 3)
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/branch",
            json={"from_step": 0, "note": "test branch"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert "branch_id" in resp.json()

    async def test_branch_out_of_range(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, session_id=sid)
        # from_step=10 >= step_count=3 → 400
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/branch",
            json={"from_step": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_branch_nonexistent_session(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/no-such/branch",
            json={"from_step": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestSessionListFilters:
    async def test_filter_by_agent_name(self, client, auth_headers, workspace_id):
        sid_a = str(uuid.uuid4())
        sid_b = str(uuid.uuid4())
        await _upload_with_agent(client, workspace_id, auth_headers, sid_a, "agent-alpha")
        await _upload_with_agent(client, workspace_id, auth_headers, sid_b, "agent-beta")
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions?agent_name=agent-alpha",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [s["id"] for s in data["items"]]
        assert sid_a in ids
        assert sid_b not in ids

    async def test_filter_by_status(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_usage(sid, status="failed", error={"type": "E", "message": "m"})
        await _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions?status=failed",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [s["id"] for s in data["items"]]
        assert sid in ids
        for item in data["items"]:
            assert item["status"] == "failed"

    async def test_pagination_limit(self, client, auth_headers, workspace_id):
        for _ in range(3):
            await _upload_with_agent(client, workspace_id, auth_headers, str(uuid.uuid4()))
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions?limit=2",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["cursor"] is not None
