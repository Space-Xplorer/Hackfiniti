"""
Tests for application input validation (P2.1 bounds checking).
"""

import pytest
from fastapi.testclient import TestClient


def _auth_header(client: TestClient) -> dict[str, str]:
    client.post("/api/auth/register", json={"email": "val@test.com", "password": "Secret123!"})
    resp = client.post("/api/auth/login", json={"email": "val@test.com", "password": "Secret123!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestApplicationValidation:
    def test_invalid_request_type_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={"request_type": "crypto"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_valid_loan_request_accepted(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={"request_type": "loan", "loan_type": "home"},
            headers=headers,
        )
        assert resp.status_code == 200

    def test_loan_amount_too_low_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "applicant_data": {"loan_amount_requested": 100},  # below ₹10,000
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_loan_amount_too_high_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "applicant_data": {"loan_amount_requested": 200_000_000},  # > ₹10Cr
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_cibil_below_300_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "applicant_data": {"cibil_score": 200},
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_cibil_above_900_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "applicant_data": {"credit_score": 950},
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_underage_applicant_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "applicant_data": {"age": 15},
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_valid_applicant_data_accepted(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "loan_type": "home",
                "applicant_data": {
                    "loan_amount_requested": 2_500_000,
                    "cibil_score": 720,
                    "age": 32,
                    "declared_monthly_income": 75000,
                },
            },
            headers=headers,
        )
        assert resp.status_code == 200

    def test_non_digit_aadhaar_rejected(self, client: TestClient):
        headers = _auth_header(client)
        resp = client.post(
            "/api/applications/",
            json={
                "request_type": "loan",
                "submitted_aadhaar": "ABCD12345678",
            },
            headers=headers,
        )
        assert resp.status_code == 422
