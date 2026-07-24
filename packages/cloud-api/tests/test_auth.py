"""Tests for auth endpoints."""

from __future__ import annotations

import asyncio
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

    async def test_signup_validation_error_never_echoes_submitted_password(
        self, client
    ):
        """P1: the 422 handler used to include Pydantic's "input" field
        verbatim — for a too-short password, that field IS the password
        itself, so it must not survive into the response body."""
        secret_value = "l3ak-me"  # 7 chars — fails min_length=8
        resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": "leak-check@example.com", "password": secret_value},
        )
        assert resp.status_code == 422
        body_text = resp.text
        assert secret_value not in body_text
        assert '"input"' not in body_text
        assert '"ctx"' not in body_text

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


class TestRateLimiting:
    """P1: brute-forcing login/signup/forgot-password must be throttled."""

    async def test_login_rate_limited_after_5_per_minute(self, client):
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "ratelimit-login@example.com",
                "password": "supersecretpassword1",
            },
        )
        statuses = []
        for _ in range(6):
            resp = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "ratelimit-login@example.com",
                    "password": "wrongpassword123",
                },
            )
            statuses.append(resp.status_code)
        assert statuses[:5] == [401] * 5
        assert statuses[5] == 429

    async def test_signup_rate_limited_after_3_per_minute(self, client):
        statuses = []
        for i in range(4):
            resp = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": f"ratelimit-signup-{i}@example.com",
                    "password": "supersecretpassword1",
                },
            )
            statuses.append(resp.status_code)
        assert statuses[:3] == [201] * 3
        assert statuses[3] == 429

    async def test_forgot_password_rate_limited_after_3_per_minute(self, client):
        statuses = []
        for _ in range(4):
            resp = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "ratelimit-forgot@example.com"},
            )
            statuses.append(resp.status_code)
        assert statuses[:3] == [200] * 3
        assert statuses[3] == 429

    async def test_rate_limit_is_scoped_per_endpoint(self, client):
        """Exhausting the login limit must not affect signup or vice versa."""
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json={"email": "no-such-user@example.com", "password": "x" * 12},
            )
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "still-allowed@example.com",
                "password": "supersecretpassword1",
            },
        )
        assert signup_resp.status_code == 201


class TestArgon2OffEventLoop:
    """P1: Argon2 hash/verify used to run directly on the event loop —
    a burst of logins could stall every other request. Both must now go
    through anyio.to_thread.run_sync()."""

    async def test_login_verifies_password_via_anyio_to_thread(
        self, client, monkeypatch
    ):
        import anyio.to_thread

        from capsule_cloud.auth import verify_password

        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "thread-check-login@example.com",
                "password": "supersecretpassword1",
            },
        )

        calls = []
        original_run_sync = anyio.to_thread.run_sync

        async def _spy_run_sync(func, *args, **kwargs):
            calls.append(func)
            return await original_run_sync(func, *args, **kwargs)

        monkeypatch.setattr(anyio.to_thread, "run_sync", _spy_run_sync)

        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "thread-check-login@example.com",
                "password": "supersecretpassword1",
            },
        )
        assert resp.status_code == 200
        assert verify_password in calls

    async def test_signup_hashes_password_via_anyio_to_thread(
        self, client, monkeypatch
    ):
        import anyio.to_thread

        from capsule_cloud.auth import hash_password

        calls = []
        original_run_sync = anyio.to_thread.run_sync

        async def _spy_run_sync(func, *args, **kwargs):
            calls.append(func)
            return await original_run_sync(func, *args, **kwargs)

        monkeypatch.setattr(anyio.to_thread, "run_sync", _spy_run_sync)

        resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "thread-check-signup@example.com",
                "password": "supersecretpassword1",
            },
        )
        assert resp.status_code == 201
        assert hash_password in calls


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

    async def test_refresh_with_malformed_token_fails(self, client):
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert resp.status_code == 401

    async def test_refresh_unauthenticated(self, client):
        resp = await client.post("/api/v1/auth/refresh")
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

    async def test_logout_revokes_provided_refresh_token(self, client):
        """P1: logout used to be a pure no-op — a refresh token handed to
        /auth/logout must actually stop working afterwards."""
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "logout-revoke@example.com",
                "password": "supersecretpassword1",
            },
        )
        refresh_token = signup_resp.json()["refresh_token"]

        logout_resp = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )
        assert logout_resp.status_code == 200

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert refresh_resp.status_code == 401

    async def test_logout_with_empty_body_still_succeeds(self, client):
        """Without a refresh_token there's nothing to revoke, but the call
        must not fail — old clients that don't send one must keep working."""
        resp = await client.post("/api/v1/auth/logout", json={})
        assert resp.status_code == 200

    async def test_logout_with_garbage_token_does_not_error(self, client):
        """Logout must be best-effort: a malformed/expired token should not
        turn a routine logout call into a 500."""
        resp = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": "not.a.valid.jwt"}
        )
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
            json={
                "email": "enum-check@example.com",
                "password": "supersecretpassword1",
            },
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
        from pydantic import ValidationError

        from capsule_cloud.config import Settings

        old = os.environ.pop("ENVIRONMENT", None)
        try:
            with pytest.raises(ValidationError):
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

    async def test_reset_password_expired_token_rejected(self, client):
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "expired-reset@example.com",
                "password": "supersecretpassword1",
            },
        )
        access_token = signup_resp.json()["access_token"]
        me_resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        user_id = me_resp.json()["id"]

        # Mint a reset token that already expired an hour ago.
        expired_token = _create_token(
            {"sub": user_id, "email": "expired-reset@example.com"},
            "password_reset",
            timedelta(hours=-1),
        )

        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": expired_token, "new_password": "newpassword1234"},
        )
        assert resp.status_code == 400

    async def test_reset_password_wrong_token_type_rejected(self, client):
        """An access token (not a password_reset token) must not work here."""
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "wrong-type-reset@example.com",
                "password": "supersecretpassword1",
            },
        )
        access_token = signup_resp.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": access_token, "new_password": "newpassword1234"},
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

    async def test_reset_password_revokes_existing_refresh_tokens(self, client):
        """P1: without this, a stolen refresh token would keep minting new
        access tokens for up to 30 days after the victim "recovered" their
        account via password reset."""
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "reset-revoke@example.com",
                "password": "supersecretpassword1",
            },
        )
        old_refresh_token = signup_resp.json()["refresh_token"]
        access_token = signup_resp.json()["access_token"]

        # JWT `iat` has 1-second resolution; make sure the revocation
        # timestamp is unambiguously after the old token's iat.
        await asyncio.sleep(1.1)

        me_resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        user_id = me_resp.json()["id"]
        reset_token = _create_token(
            {"sub": user_id, "email": "reset-revoke@example.com"},
            "password_reset",
            timedelta(hours=1),
        )

        reset_resp = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": "brandnewpassword1"},
        )
        assert reset_resp.status_code == 200

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert refresh_resp.status_code == 401

        # A token minted *after* the reset must still work.
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset-revoke@example.com", "password": "brandnewpassword1"},
        )
        assert login_resp.status_code == 200
        new_refresh_token = login_resp.json()["refresh_token"]
        refresh_resp2 = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {new_refresh_token}"},
        )
        assert refresh_resp2.status_code == 200


class TestChangePassword:
    async def test_change_password_success(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "supersecretpassword1",
                "new_password": "newpassword1234",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_change_password_wrong_current(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword1",
                "new_password": "newpassword1234",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 401

    async def test_change_password_rejected_for_oauth_account(self, client):
        """An OAuth-only account (hashed_password=None) has nothing to
        verify a "current password" against — must be rejected, not 500."""
        from capsule_cloud.auth import create_access_token
        from capsule_cloud.database import get_session_factory
        from capsule_cloud.models import User

        user_id = "oauth-test-user-id"
        session_factory = get_session_factory()
        async with session_factory() as db:
            db.add(
                User(
                    id=user_id,
                    email="oauth-user@example.com",
                    auth_provider="google",
                    hashed_password=None,
                )
            )
            await db.commit()

        oauth_access_token = create_access_token(user_id)
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "anything", "new_password": "newpassword1234"},
            headers={"Authorization": f"Bearer {oauth_access_token}"},
        )
        assert resp.status_code == 400

    async def test_change_password_unauthenticated(self, client):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "supersecretpassword1",
                "new_password": "newpassword1234",
            },
        )
        assert resp.status_code == 401

    async def test_change_password_revokes_old_refresh_tokens(self, client):
        """P1: an attacker with a stolen refresh token must be evicted the
        moment the legitimate user changes their password."""
        signup_resp = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "change-revoke@example.com",
                "password": "supersecretpassword1",
            },
        )
        access_token = signup_resp.json()["access_token"]
        old_refresh_token = signup_resp.json()["refresh_token"]

        # JWT `iat` has 1-second resolution; make sure the revocation
        # timestamp is unambiguously after the old token's iat.
        await asyncio.sleep(1.1)

        change_resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "supersecretpassword1",
                "new_password": "newpassword1234",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert change_resp.status_code == 200

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert refresh_resp.status_code == 401

        # A refresh token minted *after* the change must still work.
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "change-revoke@example.com", "password": "newpassword1234"},
        )
        assert login_resp.status_code == 200
        new_refresh_token = login_resp.json()["refresh_token"]
        refresh_resp2 = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {new_refresh_token}"},
        )
        assert refresh_resp2.status_code == 200


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
