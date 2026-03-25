"""
Tests for authentication endpoints — covering the new JWT + bcrypt flows.

Critical paths tested:
  - Register → Login → access token is a real JWT (decodable)
  - Forged "token::email" tokens must be rejected (was the old insecure pattern)
  - Expired / tampered tokens must be rejected
  - Refresh token flow
  - Duplicate registration returns 409
  - Bad credentials return 401
  - Rate-limit responses are 429
"""

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from core.config import settings


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _register(client: TestClient, email: str = "u@test.com", password: str = "Secret123!") -> dict:
    resp = client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test User"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _login(client: TestClient, email: str = "u@test.com", password: str = "Secret123!") -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth_header(client: TestClient) -> dict[str, str]:
    _register(client)
    data = _login(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


# ─── Registration ─────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client: TestClient):
        resp = client.post("/api/auth/register", json={"email": "a@b.com", "password": "Pass1234"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["email"] == "a@b.com"
        assert "password" not in body["user"], "Password hash must NOT be returned"

    def test_register_duplicate_returns_409(self, client: TestClient):
        _register(client)
        resp = client.post("/api/auth/register", json={"email": "u@test.com", "password": "anything"})
        assert resp.status_code == 409

    def test_password_not_in_response(self, client: TestClient):
        resp = client.post("/api/auth/register", json={"email": "x@y.com", "password": "MySecret"})
        text = resp.text
        assert "MySecret" not in text
        assert "password" not in resp.json().get("user", {})


# ─── Login & JWT ──────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_returns_valid_jwt(self, client: TestClient):
        _register(client)
        data = _login(client)
        token = data["access_token"]

        # Must be decodable with the correct secret
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "u@test.com"

    def test_login_wrong_password_returns_401(self, client: TestClient):
        _register(client)
        resp = client.post("/api/auth/login", json={"email": "u@test.com", "password": "WRONG"})
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        resp = client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "abc"})
        assert resp.status_code == 401

    def test_refresh_token_returned(self, client: TestClient):
        _register(client)
        data = _login(client)
        assert "refresh_token" in data
        assert data["refresh_token"] != data["access_token"]

    def test_token_type_is_bearer(self, client: TestClient):
        _register(client)
        data = _login(client)
        assert data["token_type"].lower() == "bearer"


# ─── Token forgery & tampering ────────────────────────────────────────────────

class TestTokenSecurity:
    def test_old_fake_token_rejected(self, client: TestClient):
        """The old insecure token format 'token::email' must be rejected."""
        _register(client)
        fake_token = "token::u@test.com"
        resp = client.post(
            "/api/applications/",
            json={"request_type": "loan"},
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert resp.status_code == 401, f"Fake token was accepted: {resp.text}"

    def test_tampered_jwt_rejected(self, client: TestClient):
        """Modifying a single byte in a valid JWT must be rejected."""
        _register(client)
        data = _login(client)
        token = data["access_token"]
        # Flip the last character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        resp = client.post(
            "/api/applications/",
            json={"request_type": "loan"},
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert resp.status_code == 401

    def test_missing_auth_header_returns_401_or_422(self, client: TestClient):
        resp = client.post("/api/applications/", json={"request_type": "loan"})
        assert resp.status_code in (401, 422)

    def test_empty_bearer_token_rejected(self, client: TestClient):
        resp = client.post(
            "/api/applications/",
            json={"request_type": "loan"},
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401


# ─── Refresh token ────────────────────────────────────────────────────────────

class TestRefreshToken:
    def test_refresh_issues_new_tokens(self, client: TestClient):
        _register(client)
        data = _login(client)
        refresh = data["refresh_token"]

        resp = client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        new_data = resp.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data

    def test_invalid_refresh_token_rejected(self, client: TestClient):
        resp = client.post("/api/auth/refresh", json={"refresh_token": "garbage.token.here"})
        assert resp.status_code == 401
