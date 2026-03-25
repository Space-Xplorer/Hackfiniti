from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    register_payload = {
        "email": email,
        "password": "Pass@1234",
        "name": "Test User",
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


def test_full_system_flow_submit_status_results(
    client: TestClient,
    sample_document_payloads: list[dict],
):
    headers = _auth_headers(client, email="owner@example.com")

    create_payload = {
        "request_type": "both",
        "loan_type": "home",
        "submitted_name": "Priya",
        "submitted_dob": "1994-02-01",
        "submitted_aadhaar": "123412341234",
        "applicant_data": {
            "name": "Priya",
            "age": 31,
            "credit_score": 742,
            "declared_monthly_income": 85000,
            "declared_existing_emi": 12000,
            "loan_amount_requested": 2500000,
            "property_value": 4200000,
            "employment_type": "Salaried",
            "total_work_experience": 6,
            "current_company_tenure": 3,
            "height": 168,
            "weight": 66,
            "smoker": False,
            "sum_insured": 800000,
            "pre_existing_diseases": ["none"],
            "family_history": [],
        },
        "uploaded_documents": sample_document_payloads,
    }

    create_response = client.post(
        "/api/applications/",
        json=create_payload,
        headers=headers,
    )
    assert create_response.status_code == 200
    application_id = create_response.json()["application"]["id"]

    submit_response = client.post(
        f"/api/workflow/submit/{application_id}",
        headers=headers,
    )
    assert submit_response.status_code == 200
    submit_body = submit_response.json()
    assert submit_body["app_id"] == application_id
    assert submit_body["status"] == "processing"

    status_response = client.get(
        f"/api/workflow/status/{application_id}",
        headers=headers,
    )
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["app_id"] == application_id
    assert status_body["status"] in {"completed", "failed"}
    assert "agent_errors" in status_body

    results_response = client.get(
        f"/api/workflow/results/{application_id}",
        headers=headers,
    )
    assert results_response.status_code == 200
    results_body = results_response.json()

    assert results_body["app_id"] == application_id
    assert results_body["completed"] is True
    assert "loan" in results_body
    assert "insurance" in results_body
    assert "prediction" in results_body["loan"]
    assert "explanation" in results_body["loan"]
    assert "prediction" in results_body["insurance"]
    assert "explanation" in results_body["insurance"]
    assert "verification_result" in results_body
    assert "ocr_confidence_scores" in results_body


def test_workflow_access_control_for_status_and_results(
    client: TestClient,
    sample_document_payloads: list[dict],
):
    owner_headers = _auth_headers(client, email="owner2@example.com")
    other_headers = _auth_headers(client, email="other@example.com")

    create_response = client.post(
        "/api/applications/",
        json={
            "request_type": "loan",
            "loan_type": "home",
            "submitted_name": "Rajesh",
            "submitted_dob": "1992-05-10",
            "submitted_aadhaar": "234523452345",
            "applicant_data": {
                "name": "Rajesh",
                "age": 34,
                "credit_score": 700,
                "declared_monthly_income": 70000,
                "declared_existing_emi": 10000,
                "loan_amount_requested": 1800000,
                "property_value": 3000000,
            },
            "uploaded_documents": sample_document_payloads[:3],
        },
        headers=owner_headers,
    )
    assert create_response.status_code == 200
    app_id = create_response.json()["application"]["id"]

    submit_response = client.post(
        f"/api/workflow/submit/{app_id}",
        headers=owner_headers,
    )
    assert submit_response.status_code == 200

    forbidden_status = client.get(
        f"/api/workflow/status/{app_id}",
        headers=other_headers,
    )
    assert forbidden_status.status_code == 403

    forbidden_results = client.get(
        f"/api/workflow/results/{app_id}",
        headers=other_headers,
    )
    assert forbidden_results.status_code == 403


def test_workflow_stream_endpoint_emits_events(
    client: TestClient,
    sample_document_payloads: list[dict],
):
    headers = _auth_headers(client, email="stream-owner@example.com")

    create_response = client.post(
        "/api/applications/",
        json={
            "request_type": "loan",
            "loan_type": "home",
            "submitted_name": "Priya",
            "submitted_dob": "1994-02-01",
            "submitted_aadhaar": "123412341234",
            "applicant_data": {
                "name": "Priya",
                "age": 31,
                "credit_score": 742,
                "declared_monthly_income": 85000,
                "declared_existing_emi": 12000,
                "loan_amount_requested": 2500000,
                "property_value": 4200000,
            },
            "uploaded_documents": sample_document_payloads[:4],
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    application_id = create_response.json()["application"]["id"]

    submit_response = client.post(
        f"/api/workflow/submit/{application_id}",
        headers=headers,
    )
    assert submit_response.status_code == 200

    stream_response = client.get(
        f"/api/workflow/stream/{application_id}",
        headers=headers,
    )
    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"].startswith("text/event-stream")

    body = stream_response.text
    assert "\"agent\": \"kyc\"" in body
    assert "\"done\": true" in body


def test_rejected_kyc_does_not_return_approval_summary(
    client: TestClient,
    sample_document_payloads: list[dict],
):
    headers = _auth_headers(client, email="rejected@example.com")

    create_response = client.post(
        "/api/applications/",
        json={
            "request_type": "loan",
            "loan_type": "home",
            "submitted_name": "",
            "submitted_dob": "1990-01-01",
            "submitted_aadhaar": "12345",
            "applicant_data": {
                "age": 31,
                "credit_score": 740,
                "declared_monthly_income": 85000,
                "declared_existing_emi": 5000,
            },
            "uploaded_documents": sample_document_payloads[:3],
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    application_id = create_response.json()["application"]["id"]

    submit_response = client.post(
        f"/api/workflow/submit/{application_id}",
        headers=headers,
    )
    assert submit_response.status_code == 200

    status_response = client.get(
        f"/api/workflow/status/{application_id}",
        headers=headers,
    )
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["rejected"] is True
    assert "rejection_reason" in status_body
    assert "Aadhaar" in status_body["rejection_reason"]  # Changed to fuzzy match since reason string got specific in KYC cleanup

    results_response = client = client.get(
        f"/api/workflow/results/{application_id}",
        headers=headers,
    )
    assert results_response.status_code == 200
    results_body = results_response.json()

    assert results_body["loan"]["prediction"] == {}
    assert results_body["loan"]["explanation"] == ""
    assert results_body["model_output"] == {}
    assert results_body["verification_result"].get("recommendation") == "REJECT"
