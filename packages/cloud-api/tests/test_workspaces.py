"""Tests for workspace CRUD and member management endpoints."""

from __future__ import annotations

import pytest


class TestWorkspaceList:
    def test_list_workspaces_returns_default(self, client, auth_headers):
        resp = client.get("/api/v1/workspaces", headers=auth_headers)
        assert resp.status_code == 200
        workspaces = resp.json()
        assert isinstance(workspaces, list)
        # Auto-created workspace from signup
        assert len(workspaces) >= 1

    def test_list_workspaces_unauthenticated(self, client):
        resp = client.get("/api/v1/workspaces")
        assert resp.status_code == 401


class TestWorkspaceCreate:
    def test_create_workspace(self, client, auth_headers):
        resp = client.post(
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

    def test_create_workspace_duplicate_slug(self, client, auth_headers):
        client.post(
            "/api/v1/workspaces",
            json={"name": "WS 1", "slug": "duplicate-slug"},
            headers=auth_headers,
        )
        resp = client.post(
            "/api/v1/workspaces",
            json={"name": "WS 2", "slug": "duplicate-slug"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_create_workspace_invalid_slug(self, client, auth_headers):
        resp = client.post(
            "/api/v1/workspaces",
            json={"name": "WS", "slug": "Has Spaces!"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestWorkspaceGet:
    def test_get_workspace(self, client, auth_headers, workspace_id):
        resp = client.get(f"/api/v1/workspaces/{workspace_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == workspace_id

    def test_get_workspace_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/workspaces/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404


class TestWorkspaceUpdate:
    def test_update_workspace_name(self, client, auth_headers, workspace_id):
        resp = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Renamed Workspace"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Workspace"


class TestMembers:
    def test_list_members(self, client, auth_headers, workspace_id):
        resp = client.get(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) >= 1
        assert members[0]["role"] == "owner"

    def test_invite_nonexistent_user(self, client, auth_headers, workspace_id):
        resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "ghost@nowhere.com", "role": "member"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_invite_invalid_role(self, client, auth_headers, workspace_id):
        resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "testuser@example.com", "role": "superadmin"},
            headers=auth_headers,
        )
        assert resp.status_code == 422
