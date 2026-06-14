"""Tests for workspace CRUD and member management endpoints."""

from __future__ import annotations


class TestWorkspaceList:
    async def test_list_workspaces_returns_default(self, client, auth_headers):
        resp = await client.get("/api/v1/workspaces", headers=auth_headers)
        assert resp.status_code == 200
        workspaces = resp.json()
        assert isinstance(workspaces, list)
        assert len(workspaces) >= 1

    async def test_list_workspaces_unauthenticated(self, client):
        resp = await client.get("/api/v1/workspaces")
        assert resp.status_code == 401


class TestWorkspaceCreate:
    async def test_create_workspace(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "My New WS", "slug": "my-new-ws"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My New WS"
        assert data["slug"] == "my-new-ws"
        assert data["plan_tier"] == "free"
        assert data["retention_days"] == 30

    async def test_create_workspace_duplicate_slug(self, client, auth_headers):
        await client.post(
            "/api/v1/workspaces",
            json={"name": "WS 1", "slug": "duplicate-slug"},
            headers=auth_headers,
        )
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "WS 2", "slug": "duplicate-slug"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_create_workspace_invalid_slug(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "WS", "slug": "Has Spaces!"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestWorkspaceGet:
    async def test_get_workspace(self, client, auth_headers, workspace_id):
        resp = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == workspace_id

    async def test_get_workspace_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/workspaces/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404


class TestWorkspaceUpdate:
    async def test_update_workspace_name(self, client, auth_headers, workspace_id):
        resp = await client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Renamed Workspace"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Workspace"


class TestMembers:
    async def test_list_members(self, client, auth_headers, workspace_id):
        resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) >= 1
        assert members[0]["role"] == "owner"

    async def test_invite_nonexistent_user(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "ghost@nowhere.com", "role": "member"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_invite_invalid_role(self, client, auth_headers, workspace_id):
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "testuser@example.com", "role": "superadmin"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestWorkspaceDelete:
    async def test_delete_workspace(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "Delete Me", "slug": "delete-me-ws"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        ws_id = resp.json()["id"]
        resp = await client.delete(f"/api/v1/workspaces/{ws_id}", headers=auth_headers)
        assert resp.status_code == 204
        resp = await client.get(f"/api/v1/workspaces/{ws_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_delete_workspace_nonexistent(self, client, auth_headers):
        resp = await client.delete("/api/v1/workspaces/does-not-exist", headers=auth_headers)
        assert resp.status_code in (403, 404)


class TestMemberInviteSuccess:
    async def test_invite_existing_user(self, client, auth_headers, workspace_id):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "invitee@example.com", "password": "supersecretpassword1"},
        )
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "invitee@example.com", "role": "member"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "member"
        assert "user_id" in data

    async def test_invite_same_user_twice(self, client, auth_headers, workspace_id):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "invitee2@example.com", "password": "supersecretpassword1"},
        )
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "invitee2@example.com", "role": "member"},
            headers=auth_headers,
        )
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "invitee2@example.com", "role": "member"},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestMemberRemove:
    async def _invite_user(self, client, auth_headers, workspace_id, email):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "supersecretpassword1"},
        )
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": email, "role": "member"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        return resp.json()["user_id"]

    async def test_remove_member(self, client, auth_headers, workspace_id):
        user_id = await self._invite_user(client, auth_headers, workspace_id, "toremove@example.com")
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/{user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_remove_owner_fails(self, client, auth_headers, workspace_id):
        me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        owner_id = me_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/{owner_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_remove_nonexistent_member(self, client, auth_headers, workspace_id):
        resp = await client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/does-not-exist",
            headers=auth_headers,
        )
        assert resp.status_code == 404
