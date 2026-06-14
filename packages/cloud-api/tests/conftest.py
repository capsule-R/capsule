"""Shared pytest fixtures for Cloud API tests.

Strategy: each test gets its own file-based SQLite database via tmp_path.
We reset the get_settings() singleton and DATABASE_URL so that both
create_tables() and get_db() use the same isolated DB.

Using httpx.AsyncClient with ASGITransport so async router code runs in the
same event loop as the test — this ensures coverage.py can track it.
"""

from __future__ import annotations

import os

import httpx
import pytest_asyncio


@pytest_asyncio.fixture
async def client(tmp_path):
    """Fresh async HTTP client backed by an isolated SQLite file."""
    import capsule_cloud.config as cfg
    import capsule_cloud.database as dbmod

    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

    old_settings = cfg._settings
    old_engine = dbmod._engine
    old_factory = dbmod._session_factory
    cfg._settings = None
    dbmod._engine = None
    dbmod._session_factory = None
    os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-32-bytes-xx")

    try:
        from capsule_cloud.database import create_tables
        from capsule_cloud.main import create_app

        app = create_app()
        await create_tables()  # replaces TestClient lifespan startup
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            yield c
    finally:
        del os.environ["DATABASE_URL"]
        cfg._settings = old_settings
        dbmod._engine = old_engine
        dbmod._session_factory = old_factory


@pytest_asyncio.fixture
async def auth_headers(client):
    """Sign up a test user and return Bearer auth headers."""
    resp = await client.post(
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


@pytest_asyncio.fixture
async def workspace_id(client, auth_headers):
    """Return the ID of the auto-created workspace for the test user."""
    resp = await client.get("/api/v1/workspaces", headers=auth_headers)
    assert resp.status_code == 200, resp.json()
    workspaces = resp.json()
    assert len(workspaces) >= 1, "Expected at least one workspace after signup"
    return workspaces[0]["id"]
