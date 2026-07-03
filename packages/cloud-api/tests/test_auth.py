"""Tests for auth endpoints."""

from __future__ import annotations

from datetime import timedelta

from capsule_cloud.auth import _create_token


class TestSignup:
    async def test_signup_success(self, client):
        resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "new@example.com",
                "password": "supersecretpassword1",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_signup_duplicate_email(self, client):
        payload = {
            "email": "dup@example.com",
            "password": "supersecretpassword1",
        }
        await client.post("/api/v1/auth/signup", json=payload)
        resp = await client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code == 409

    async def test_signup_password_too_short(self, client):
        resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "short@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    async def test_signup_invalid_email(self, client):
        resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "notanemail", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "login@example.com", "password": "supersecretpassword1"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "login2@example.com", "password": "supersecretpassword1"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login2@example.com", "password": "wrongpassword123"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_user(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, client):
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh@example.com", "password": "supersecretpassword1"},
        )
        refresh_token = signup_resp.json()["refresh_token"]
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token_fails(self, client):
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh2@example.com", "password": "supersecretpassword1"},
        )
        access_token = signup_resp.json()["access_token"]
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_get_me_authenticated(self, client, auth_headers):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "testuser@example.com"

    async def test_get_me_unauthenticated(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestLogout:
    async def test_logout(self, client, auth_headers):
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"

    async def test_logout_unauthenticated(self, client):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200


class TestForgotPassword:
    async def test_forgot_password_existing_user_never_echoes_token(self, client):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "forgot@example.com", "password": "supersecretpassword1"},
        )
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgot@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # P0-1: the token must never be echoed in the HTTP response, in any
        # environment — a forgotten ENVIRONMENT setting in production must not
        # turn this endpoint into an unauthenticated account-takeover primitive.
        assert "reset_token" not in data
        assert set(data.keys()) == {"message"}

    async def test_forgot_password_nonexistent_user(self, client):
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
        assert resp.status_code == 200
        # Must not leak whether the account exists
        assert "reset_token" not in resp.json()

    async def test_forgot_password_existing_and_nonexistent_responses_are_identical(
        self, client
    ):
        """The response body must be indistinguishable regardless of account
        existence — otherwise the endpoint is a user-enumeration oracle."""
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "enum-check@example.com", "password": "supersecretpassword1"},
        )
        resp_existing = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "enum-check@example.com"},
        )
        resp_missing = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "definitely-not-registered@example.com"},
        )
        assert resp_existing.status_code == resp_missing.status_code == 200
        assert resp_existing.json() == resp_missing.json()

    async def test_forgot_password_rejects_settings_without_environment(self):
        """P0-1: Settings() must fail to construct if ENVIRONMENT is unset —
        the old default of "development" was a fail-open trap."""
        import os

        import pytest

        from capsule_cloud.config import Settings

        old = os.environ.pop("ENVIRONMENT", None)
        try:
            with pytest.raises(Exception):
                Settings(_env_file=None)
        finally:
            if old is not None:
                os.environ["ENVIRONMENT"] = old

    async def test_forgot_password_rejects_invalid_environment_value(self):
        from capsule_cloud.config import Settings

        try:
            Settings(environment="dev", _env_file=None)
            raised = False
        except Exception:
            raised = True
        assert raised, "an unrecognized ENVIRONMENT value must be rejected"


class TestResetPassword:
    async def _register_and_get_token(self, client, email="resetme@example.com"):
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "supersecretpassword1"},
        )
        access_token = signup_resp.json()["access_token"]
        me_resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        user_id = me_resp.json()["id"]

        # forgot-password no longer returns the token (P0-1) — mint an
        # equivalent one the same way the endpoint does internally, to
        # exercise the reset-password flow end to end.
        token = _create_token(
            {"sub": user_id, "email": email}, "password_reset", timedelta(hours=1)
        )

        resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        assert "reset_token" not in resp.json()

        return token, email

    async def test_reset_password_success(self, client):
        token, email = await self._register_and_get_token(client)
        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "newpassword1234"},
        )
        assert resp.status_code == 200
        # Verify new password works for login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "newpassword1234"},
        )
        assert login_resp.status_code == 200

    async def test_reset_password_invalid_token(self, client):
        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "not.a.valid.jwt", "new_password": "newpassword1234"},
        )
        assert resp.status_code == 400

    async def test_reset_password_token_replay_rejected(self, client):
        token, _ = await self._register_and_get_token(client, "replay@example.com")
        # First use succeeds
        resp1 = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "newpassword1234"},
        )
        assert resp1.status_code == 200
        # Second use with the same token (same jti) must be rejected
        resp2 = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "anotherpassword99"},
        )
        assert resp2.status_code == 400


class TestChangePassword:
    async def test_change_password_success(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "supersecretpassword1", "new_password": "newpassword1234"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_change_password_wrong_current(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "wrongpassword1", "new_password": "newpassword1234"},
            headers=auth_headers,
        )
        assert resp.status_code == 401

    async def test_change_password_unauthenticated(self, client):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "supersecretpassword1", "new_password": "newpassword1234"},
        )
        assert resp.status_code == 401


class TestUpdateMe:
    async def test_update_full_name(self, client, auth_headers):
        resp = await client.patch(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    async def test_update_email_conflict(self, client, auth_headers):
        await client.post(
            "/api/v1/auth/signup",
            json={"email": "other@example.com", "password": "supersecretpassword1"},
        )
        resp = await client.patch(
            "/api/v1/auth/me",
            json={"email": "other@example.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_update_unauthenticated(self, client):
        resp = await client.patch("/api/v1/auth/me", json={"full_name": "Hacker"})
        assert resp.status_code == 401
