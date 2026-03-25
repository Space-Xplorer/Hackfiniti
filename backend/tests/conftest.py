"""
Shared test fixtures.

Key design decisions:
  - TEST_MODE=true is set before main.py is imported so the Limiter's key_func
    returns a unique key per request, preventing rate-limit interference.
  - In-memory state DBs are wiped before and after every test function.
"""

import base64
import os
from pathlib import Path

# ── Must be set BEFORE main.py (and therefore slowapi) is imported ──────────
os.environ.setdefault("TEST_MODE", "true")

import pytest
from fastapi.testclient import TestClient

from api.state import APPLICATIONS_DB, OTP_DB, USERS_DB, WORKFLOW_DB, WORKFLOW_EVENTS
from main import app


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    USERS_DB.clear()
    APPLICATIONS_DB.clear()
    WORKFLOW_DB.clear()
    WORKFLOW_EVENTS.clear()
    OTP_DB.clear()
    yield
    USERS_DB.clear()
    APPLICATIONS_DB.clear()
    WORKFLOW_DB.clear()
    WORKFLOW_EVENTS.clear()
    OTP_DB.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_document_payloads() -> list[dict]:
    project_root = Path(__file__).resolve().parents[2]
    docs_root = project_root / "temp" / "temp"

    documents = [
        ("aadhaar_card", "sample_id_proof.pdf"),
        ("salary_slip", "sample_salary_slip.pdf"),
        ("bank_statement", "sample_bank_statement.pdf"),
        ("property_document", "sample_property_sale_agreement.pdf"),
        ("diagnostic_report", "sample_medical_report.pdf"),
        ("pan_card", "priya_pan_card.pdf"),
        ("salary_slip", "rajesh_kumar_3_month_salary_slip.pdf"),
    ]

    payloads: list[dict] = []
    for doc_type, filename in documents:
        file_path = docs_root / filename
        encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        payloads.append(
            {
                "type": doc_type,
                "name": filename,
                "mime_type": "application/pdf",
                "content_base64": encoded,
            }
        )

    return payloads
