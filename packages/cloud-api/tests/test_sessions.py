"""Tests for session upload, list, get, and delete endpoints."""

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


def _upload_session(client, workspace_id, auth_headers, session_id=None):
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
    return client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
        data={"metadata": metadata},
        headers=auth_headers,
    )


class TestSessionUpload:
    def test_upload_success(self, client, auth_headers, workspace_id):
        resp = _upload_session(client, workspace_id, auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["workspace_id"] == workspace_id
        assert data["agent_name"] == "test-agent"
        assert data["status"] == "completed"
        assert data["tags"] == ["test"]

    def test_upload_duplicate_session_id(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        resp1 = _upload_session(client, workspace_id, auth_headers, session_id=sid)
        assert resp1.status_code == 201
        resp2 = _upload_session(client, workspace_id, auth_headers, session_id=sid)
        assert resp2.status_code == 409

    def test_upload_invalid_metadata_json(self, client, auth_headers, workspace_id):
        capsule_bytes = _make_capsule_bytes()
        resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
            data={"metadata": "this is not json"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_upload_unauthenticated(self, client, workspace_id):
        capsule_bytes = _make_capsule_bytes()
        resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
            data={"metadata": "{}"},
        )
        assert resp.status_code == 401


class TestSessionList:
    def test_list_empty(self, client, auth_headers):
        # Create a fresh workspace
        resp = client.post(
            "/api/v1/workspaces",
            json={"name": "List Test", "slug": "list-test-ws-2"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        ws_id = resp.json()["id"]
        resp = client.get(
            f"/api/v1/workspaces/{ws_id}/sessions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_after_upload(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [s["id"] for s in data["items"]]
        assert sid in ids


class TestSessionGet:
    def test_get_existing_session(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    def test_get_nonexistent_session(self, client, auth_headers, workspace_id):
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/does-not-exist",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestSessionDelete:
    def test_delete_session(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = client.delete(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
        # Verify it's gone
        resp2 = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}",
            headers=auth_headers,
        )
        assert resp2.status_code == 404


# ── Cost / token extraction ───────────────────────────────────

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


def _upload_capsule(client, workspace_id, auth_headers, sid, capsule_bytes):
    metadata = json.dumps(
        {"session_id": sid, "agent_name": "test-agent", "agent_version": "1.0.0",
         "tags": [], "user_metadata": {}, "auto_redact": False}
    )
    return client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={"file": ("test.capsule", io.BytesIO(capsule_bytes), "application/octet-stream")},
        data={"metadata": metadata},
        headers=auth_headers,
    )


class TestCostTokenExtraction:
    def test_cost_and_tokens_extracted(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_usage(sid, cost=0.0171, in_tok=1200, out_tok=340)
        resp = _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert abs(data["total_cost_usd"] - 0.0171) < 1e-6
        assert data["total_input_tokens"] == 1200
        assert data["total_output_tokens"] == 340

    def test_nested_error_extracted(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        cap = _make_capsule_with_usage(
            sid, status="failed", error={"type": "ValueError", "message": "boom"}
        )
        resp = _upload_capsule(client, workspace_id, auth_headers, sid, cap)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error_type"] == "ValueError"
        assert data["error_message"] == "boom"


class TestSessionStats:
    def test_stats_empty(self, client, auth_headers):
        resp = client.post(
            "/api/v1/workspaces",
            json={"name": "Stats WS", "slug": "stats-ws-empty"},
            headers=auth_headers,
        )
        ws_id = resp.json()["id"]
        resp = client.get(
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

    def test_stats_after_uploads(self, client, auth_headers, workspace_id):
        ok = str(uuid.uuid4())
        bad = str(uuid.uuid4())
        _upload_capsule(client, workspace_id, auth_headers, ok,
                        _make_capsule_with_usage(ok, cost=0.10, in_tok=10, out_tok=5))
        _upload_capsule(client, workspace_id, auth_headers, bad,
                        _make_capsule_with_usage(bad, status="failed",
                                                 error={"type": "E", "message": "m"}))
        resp = client.get(
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

    def test_stats_route_not_shadowed_by_session_id(self, client, auth_headers, workspace_id):
        # "stats" must hit the stats endpoint, not be treated as a session id.
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/stats", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "daily" in resp.json()


class TestSessionDownload:
    def test_download_capsule(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        _upload_session(client, workspace_id, auth_headers, session_id=sid)
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/download",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert sid in resp.headers.get("content-disposition", "")
        # Body is the raw zstd-compressed .capsule — decompresses to a tar with session.json
        tar_bytes = zstd.ZstdDecompressor().decompress(resp.content)
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
            names = tar.getnames()
        assert any(n.endswith("session.json") for n in names)

    def test_download_nonexistent(self, client, auth_headers, workspace_id):
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/sessions/nope/download",
            headers=auth_headers,
        )
        assert resp.status_code == 404
