"""Tests for API key management endpoints."""

from __future__ import annotations


class TestApiKeyCreate:
    async def test_create_api_key(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"name": "CI Key"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "CI Key"
        assert data["full_key"] is not None
        assert data["full_key"].startswith("csk_")
        assert len(data["key_prefix"]) == 12
        assert data["expires_at"] is None

    async def test_create_api_key_with_expiry(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"name": "Expiring Key", "expires_at": "2030-01-01T00:00:00Z"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["expires_at"] is not None

    async def test_create_api_key_name_required(
        self, client, auth_headers, workspace_id
    ):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_full_key_not_returned_on_list(
        self, client, auth_headers, workspace_id
    ):
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"name": "Secret Key"},
            headers=auth_headers,
        )
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for key in resp.json():
            assert key.get("full_key") is None


class TestApiKeyList:
    async def test_list_api_keys(self, client, auth_headers, workspace_id):
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"name": "List Key"},
            headers=auth_headers,
        )
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_list_unauthenticated(self, client, workspace_id):
        resp = await client.get(f"/api/v1/workspaces/{workspace_id}/api-keys")
        assert resp.status_code == 401


class TestApiKeyRevoke:
    async def test_revoke_api_key(self, client, auth_headers, workspace_id):
        create_resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"name": "To Revoke"},
            headers=auth_headers,
        )
        key_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/api-keys/{key_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
        list_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            headers=auth_headers,
        )
        ids = [k["id"] for k in list_resp.json()]
        assert key_id not in ids

    async def test_revoke_nonexistent_key(self, client, auth_headers, workspace_id):
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/api-keys/nonexistent",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestHealthCheck:
    async def test_health(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data
