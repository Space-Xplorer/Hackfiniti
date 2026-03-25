import base64


def _auth_headers(client, email: str) -> dict[str, str]:
    register_payload = {
        "email": email,
        "password": "Pass@1234",
        "name": "Workflow Test User",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Pass@1234"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _fake_png_bytes(size: int = 1200) -> bytes:
    header = b"\x89PNG\r\n\x1a\n"
    payload = b"A" * max(0, size - len(header))
    return header + payload


def test_preview_ocr_accepts_png_document(client):
    headers = _auth_headers(client, "ocr-png@example.com")

    png_doc = {
        "type": "aadhaar_card",
        "name": "aadhaar_card_scan.png",
        "mime_type": "image/png",
        "content_base64": base64.b64encode(_fake_png_bytes()).decode("utf-8"),
    }

    payload = {
        "request_type": "loan",
        "declared_data": {
            "name": "Test User",
            "dob": "1995-01-01",
        },
        "uploaded_documents": [
            png_doc,
            {
                "type": "salary_slip",
                "name": "salary_slip.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"B" * 1100).decode("utf-8"),
            },
            {
                "type": "bank_statement",
                "name": "bank_statement.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"C" * 1100).decode("utf-8"),
            },
        ],
    }

    response = client.post("/api/workflow/preview-ocr", json=payload, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ocr_status"] == "success"
    assert "confidence_scores" in body
    assert "aadhaar_card" in body["confidence_scores"]


def test_preview_ocr_rejects_voter_id_uploaded_as_aadhaar(client):
    headers = _auth_headers(client, "ocr-mismatch@example.com")

    mismatched_doc = {
        "type": "aadhaar_card",
        "name": "voter_id_front.png",
        "mime_type": "image/png",
        "content_base64": base64.b64encode(_fake_png_bytes()).decode("utf-8"),
    }

    payload = {
        "request_type": "loan",
        "declared_data": {"name": "Mismatch User"},
        "uploaded_documents": [
            mismatched_doc,
            {
                "type": "salary_slip",
                "name": "salary_slip.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"D" * 1100).decode("utf-8"),
            },
            {
                "type": "bank_statement",
                "name": "bank_statement.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"E" * 1100).decode("utf-8"),
            },
        ],
    }

    response = client.post("/api/workflow/preview-ocr", json=payload, headers=headers)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "errors" in detail
    assert any("appears to be 'voter id'" in err.lower() for err in detail["errors"])


def test_preview_ocr_flags_missing_required_info(client):
    headers = _auth_headers(client, "ocr-missing-required@example.com")

    payload = {
        "request_type": "loan",
        "declared_data": {
            "name": "Missing Fields User",
            "dob": "1991-08-21",
        },
        "uploaded_documents": [
            {
                "type": "aadhaar_card",
                "name": "aadhaar_card.png",
                "mime_type": "image/png",
                "content_base64": base64.b64encode(_fake_png_bytes()).decode("utf-8"),
            },
            {
                "type": "salary_slip",
                "name": "salary_slip.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"S" * 1100).decode("utf-8"),
            },
            {
                "type": "bank_statement",
                "name": "bank_statement.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4\n" + b"B" * 1100).decode("utf-8"),
            },
        ],
    }

    response = client.post("/api/workflow/preview-ocr", json=payload, headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert body["required_info_complete"] is False
    assert "missing_required_fields" in body
    assert "declared_monthly_income" in body["missing_required_fields"]
    assert "declared_existing_emi" in body["missing_required_fields"]
