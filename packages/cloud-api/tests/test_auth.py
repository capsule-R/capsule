"""Tests for auth endpoints."""

from __future__ import annotations

import pytest


class TestSignup:
    def test_signup_success(self, client):
        resp = client.post(
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

    def test_signup_duplicate_email(self, client):
        payload = {
            "email": "dup@example.com",
            "password": "supersecretpassword1",
        }
        client.post("/api/v1/auth/signup", json=payload)
        resp = client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code == 409

    def test_signup_password_too_short(self, client):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "short@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    def test_signup_invalid_email(self, client):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "notanemail", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post(
            "/api/v1/auth/signup",
            json={"email": "login@example.com", "password": "supersecretpassword1"},
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post(
            "/api/v1/auth/signup",
            json={"email": "login2@example.com", "password": "supersecretpassword1"},
        )
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "login2@example.com", "password": "wrongpassword123"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "supersecretpassword1"},
        )
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_success(self, client):
        signup_resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh@example.com", "password": "supersecretpassword1"},
        )
        refresh_token = signup_resp.json()["refresh_token"]
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_with_access_token_fails(self, client):
        signup_resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh2@example.com", "password": "supersecretpassword1"},
        )
        access_token = signup_resp.json()["access_token"]
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_get_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "testuser@example.com"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
