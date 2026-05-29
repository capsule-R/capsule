"""Shared pytest fixtures for Cloud API tests.

Strategy: each test gets its own file-based SQLite database via tmp_path.
We reset the get_settings() singleton and set DATABASE_URL so that both
create_tables() (lifespan) and get_db() (dependency) use the same DB.

NOTE: SQLite async requires the `aiosqlite` package (add to dev dependencies).
"""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    """Fresh FastAPI TestClient backed by an isolated SQLite file."""
    import capsule_cloud.config as cfg

    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

    # Reset the singleton so get_settings() re-reads env vars
    old_settings = cfg._settings
    cfg._settings = None
    os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-32-bytes-xx")

    try:
        from capsule_cloud.main import create_app
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        # Restore env + singleton
        del os.environ["DATABASE_URL"]
        cfg._settings = old_settings


@pytest.fixture
def auth_headers(client):
    """Sign up a test user and return Bearer auth headers."""
    resp = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "supersecretpassword1",
            "full_name": "Test User",
        },
    )
    assert resp.status_code == 201, resp.json()
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    """Return the ID of the auto-created workspace for the test user."""
    resp = client.get("/api/v1/workspaces", headers=auth_headers)
    assert resp.status_code == 200, resp.json()
    workspaces = resp.json()
    assert len(workspaces) >= 1, "Expected at least one workspace after signup"
    return workspaces[0]["id"]
