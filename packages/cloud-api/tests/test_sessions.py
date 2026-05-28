"""Tests for session upload, list, get, and delete endpoints."""

from __future__ import annotations

import io
import json
import tarfile
import uuid

import pytest
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
