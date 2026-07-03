"""P0-3 regression tests — replay status must be a real, persisted result,
never a fabricated verdict, and must be scoped to the requester's workspace."""

from __future__ import annotations

import io
import json
import tarfile
import uuid

import zstandard as zstd


def _make_capsule_bytes(session_id: str) -> bytes:
    session_data = {
        "session_id": session_id,
        "agent_name": "test-agent",
        "status": "completed",
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:01:00+00:00",
        "duration_ms": 60000,
        "step_count": 0,
    }
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        b = json.dumps(session_data).encode()
        info = tarfile.TarInfo(name="session.json")
        info.size = len(b)
        tar.addfile(info, io.BytesIO(b))
    return zstd.ZstdCompressor().compress(tar_buf.getvalue())


async def _upload_session(client, workspace_id, auth_headers, session_id):
    metadata = json.dumps(
        {
            "session_id": session_id,
            "agent_name": "test-agent",
            "agent_version": "1.0.0",
            "tags": [],
            "user_metadata": {},
            "auto_redact": False,
        }
    )
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/sessions",
        files={
            "file": (
                "test.capsule",
                io.BytesIO(_make_capsule_bytes(session_id)),
                "application/octet-stream",
            )
        },
        data={"metadata": metadata},
        headers=auth_headers,
    )


async def _signup(client, email: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "supersecretpassword1"},
    )
    assert resp.status_code == 201, resp.json()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestReplayStatus:
    async def test_replay_status_reflects_real_local_result(
        self, client, auth_headers, workspace_id
    ):
        sid = str(uuid.uuid4())
        upload_resp = await _upload_session(client, workspace_id, auth_headers, sid)
        assert upload_resp.status_code == 201

        trigger_resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        assert trigger_resp.status_code == 202
        replay_id = trigger_resp.json()["id"]

        status_resp = await client.get(
            f"/api/v1/replays/{replay_id}", headers=auth_headers
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["replay_id"] == replay_id
        # The local-replay path resolves synchronously, so this session
        # (zero events) is immediately either completed or a reported error —
        # never a wall-clock-simulated "queued"/"running" placeholder.
        assert data["status"] in ("completed", "error")
        if data["status"] == "completed":
            # Must be the CLI's real verdict, not a hard-coded True.
            assert "is_deterministic" in data["result"]

    async def test_replay_status_nonexistent_returns_404(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/replays/nonexistent-replay-id", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_replay_status_requires_workspace_membership(
        self, client, auth_headers, workspace_id
    ):
        """P0-3 IDOR fix: an authenticated user who isn't a member of the
        replay's workspace must not be able to poll its status."""
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, sid)
        trigger_resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        replay_id = trigger_resp.json()["id"]

        outsider_headers = await _signup(client, "outsider@example.com")
        resp = await client.get(
            f"/api/v1/replays/{replay_id}", headers=outsider_headers
        )
        assert resp.status_code == 404

    async def test_replay_status_unauthenticated(self, client, auth_headers, workspace_id):
        sid = str(uuid.uuid4())
        await _upload_session(client, workspace_id, auth_headers, sid)
        trigger_resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/sessions/{sid}/replay",
            json={"mode": "cassette"},
            headers=auth_headers,
        )
        replay_id = trigger_resp.json()["id"]

        resp = await client.get(f"/api/v1/replays/{replay_id}")
        assert resp.status_code == 401
