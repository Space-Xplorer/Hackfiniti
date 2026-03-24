import asyncio
import base64
import json
import random

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from api.state import APPLICATIONS_DB, WORKFLOW_DB, WORKFLOW_EVENTS, new_id, parse_token

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Expected document types per service
REQUIRED_DOC_TYPES = {
    "loan": {"bank_statement", "salary_slip", "aadhaar_card"},
    "insurance": {"diagnostic_report", "aadhaar_card"},
}

# Fields each document type is expected to provide
DOC_FIELD_MAP = {
    "bank_statement": ["declared_monthly_income", "declared_existing_emi"],
    "salary_slip": ["declared_monthly_income", "employment_type"],
    "aadhaar_card": ["name", "dob", "gender"],
    "diagnostic_report": ["age", "height", "weight"],
    "itr": ["declared_monthly_income"],
    "loan_statement": ["declared_existing_emi"],
    "property_document": ["property_value", "property_city"],
}

# Minimum file size in bytes to be considered a real document (not a blank/random file)
MIN_DOC_SIZE_BYTES = 500


def _get_email(authorization: str | None) -> str:
    token = (authorization or "").replace("Bearer ", "", 1)
    email = parse_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return email


def _validate_documents(uploaded_documents: list[dict], request_type: str) -> tuple[list[str], dict[str, float]]:
    """
    Validates uploaded documents and returns:
    - list of validation error messages
    - dict of doc_type -> confidence score (0-100)
    """
    errors = []
    confidence_scores: dict[str, float] = {}
    uploaded_types = {doc.get("type") for doc in uploaded_documents}
    required = REQUIRED_DOC_TYPES.get(request_type, set())

    # Check required types are present
    missing = required - uploaded_types
    if missing:
        errors.append(f"Missing required documents: {', '.join(sorted(missing)).replace('_', ' ')}")

    for doc in uploaded_documents:
        doc_type = doc.get("type", "unknown")
        content_b64 = doc.get("content_base64", "")
        name = doc.get("name", "")
        mime = doc.get("mime_type", "")

        # Decode and check actual file size
        try:
            raw = base64.b64decode(content_b64 + "==")
            size = len(raw)
        except Exception:
            size = 0

        # Reject suspiciously small files (likely random/blank)
        if size < MIN_DOC_SIZE_BYTES:
            errors.append(f"'{name}' appears to be empty or corrupt (size: {size} bytes). Please upload a valid document.")
            confidence_scores[doc_type] = 0.0
            continue

        # Check MIME type matches expected for document type
        valid_mimes = {"application/pdf", "image/jpeg", "image/jpg", "image/png"}
        if mime and mime not in valid_mimes:
            errors.append(f"'{name}' has unsupported format '{mime}'. Use PDF, JPG, or PNG.")
            confidence_scores[doc_type] = 10.0
            continue

        # Simulate OCR confidence based on file size and type
        # Larger, properly-typed files get higher confidence
        base_confidence = min(95.0, 50.0 + (size / 10000) * 20)
        noise = random.uniform(-5, 5)
        confidence_scores[doc_type] = round(max(10.0, min(98.0, base_confidence + noise)), 1)

    return errors, confidence_scores


def _extract_fields(uploaded_documents: list[dict], declared_data: dict) -> dict:
    """Simulate OCR field extraction — prefill from declared data, add mock values for missing fields."""
    extracted = dict(declared_data)
    uploaded_types = {doc.get("type") for doc in uploaded_documents}

    # For each uploaded doc type, simulate extracting its fields
    mock_values = {
        "declared_monthly_income": 85000,
        "declared_existing_emi": 5000,
        "employment_type": "Salaried",
        "name": declared_data.get("name", ""),
        "dob": declared_data.get("dob", ""),
        "gender": "Male",
        "age": 31,
        "height": 170,
        "weight": 72,
        "property_value": 5000000,
        "property_city": declared_data.get("city", ""),
    }

    for doc_type in uploaded_types:
        for field in DOC_FIELD_MAP.get(doc_type, []):
            if field not in extracted or not extracted[field]:
                extracted[field] = mock_values.get(field, "")

    return extracted


@router.post("/verify-kyc")
async def verify_kyc(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    _get_email(authorization)
    if not payload.get("name") or not payload.get("aadhaar"):
        raise HTTPException(status_code=400, detail="Name and Aadhaar are required")
    aadhaar = str(payload.get("aadhaar", ""))
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Aadhaar must be exactly 12 digits")
    return {
        "verified": True,
        "kyc_data": {
            "name": payload.get("name"),
            "aadhaar_number": aadhaar,
            "dob": payload.get("dob"),
            "cibil_score": 742,
            "gender": "Male",
            "address": "Mock Address, India",
        },
    }


def _cross_validate_ocr(ocr_json: dict) -> tuple[list[str], bool]:
    """
    Server-side cross-document validation of pre-extracted OCR JSON.
    Returns (consistency_flags, freshness_passed).
    """
    flags: list[str] = []
    freshness_ok = True
    from datetime import date, datetime

    raw = ocr_json.get("raw_by_type", {})
    extracted = ocr_json.get("extracted_data", {})

    # Name consistency
    salary_name = (raw.get("salary_slip") or {}).get("employee_name", "")
    bank_name = (raw.get("bank_statement") or {}).get("account_name", "")
    id_name = (raw.get("aadhaar_card") or {}).get("full_name", "")

    def norm(s): return (s or "").strip().lower()

    if norm(salary_name) and norm(bank_name) and norm(salary_name) != norm(bank_name):
        flags.append(f"Name mismatch: Salary slip '{salary_name}' ≠ Bank account '{bank_name}'")
    if norm(salary_name) and norm(id_name) and norm(salary_name) != norm(id_name):
        flags.append(f"Name mismatch: Salary slip '{salary_name}' ≠ ID proof '{id_name}'")
    if norm(bank_name) and norm(id_name) and norm(bank_name) != norm(id_name):
        flags.append(f"Name mismatch: Bank account '{bank_name}' ≠ ID proof '{id_name}'")

    # Income consistency
    net_income = (raw.get("salary_slip") or {}).get("net_income")
    deposits = (raw.get("bank_statement") or {}).get("recurring_salary_deposits")
    if net_income and deposits:
        diff = abs(net_income - deposits) / max(net_income, 1)
        if diff > 0.2:
            flags.append(f"Income mismatch: Salary slip ₹{net_income} vs bank deposits ₹{deposits} (>{round(diff*100)}% difference)")

    # Freshness checks
    today = date.today()
    slip_date_str = (raw.get("salary_slip") or {}).get("slip_date")
    if slip_date_str:
        try:
            slip_date = datetime.strptime(slip_date_str[:10], "%Y-%m-%d").date()
            months_old = (today - slip_date).days / 30
            if months_old > 3:
                flags.append(f"Salary slip dated {slip_date_str} is older than 3 months")
                freshness_ok = False
        except ValueError:
            pass

    stmt_date_str = (raw.get("bank_statement") or {}).get("statement_date")
    if stmt_date_str:
        try:
            stmt_date = datetime.strptime(stmt_date_str[:10], "%Y-%m-%d").date()
            months_old = (today - stmt_date).days / 30
            if months_old > 6:
                flags.append(f"Bank statement dated {stmt_date_str} is older than 6 months")
                freshness_ok = False
        except ValueError:
            pass

    return flags, freshness_ok


@router.post("/preview-ocr")
async def preview_ocr(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    _get_email(authorization)

    uploaded_documents: list[dict] = payload.get("uploaded_documents") or []
    declared_data: dict = payload.get("declared_data") or {}
    request_type: str = payload.get("request_type") or "loan"
    # Pre-extracted OCR JSON from client-side Puter.js (optional)
    client_ocr: dict | None = payload.get("client_ocr")

    if not uploaded_documents and not client_ocr:
        raise HTTPException(status_code=400, detail="No documents uploaded.")

    # --- Path A: client sent pre-extracted OCR JSON ---
    if client_ocr:
        flags, freshness_ok = _cross_validate_ocr(client_ocr)
        extracted_data = client_ocr.get("extracted_data", {})
        confidence = client_ocr.get("confidence_score", 0.8)

        # Merge with declared data for prefill
        prefill = {**declared_data}
        if extracted_data.get("monthly_income"):
            prefill["declared_monthly_income"] = extracted_data["monthly_income"]
        if extracted_data.get("existing_emi"):
            prefill["declared_existing_emi"] = extracted_data["existing_emi"]
        if extracted_data.get("property_value"):
            prefill["property_value"] = extracted_data["property_value"]
        if extracted_data.get("employer_name"):
            prefill["employer_name"] = extracted_data["employer_name"]

        raw = client_ocr.get("raw_by_type", {})
        if raw.get("aadhaar_card", {}).get("full_name"):
            prefill["name"] = raw["aadhaar_card"]["full_name"]
        if raw.get("aadhaar_card", {}).get("dob"):
            prefill["dob"] = raw["aadhaar_card"]["dob"]

        return {
            "ocr_extracted_data": prefill,
            "declared_prefill": prefill,
            "consistency_flags": flags,
            "document_freshness_passed": freshness_ok,
            "confidence_score": confidence,
        }

    # --- Path B: fallback — validate raw uploaded documents ---
    errors, confidence_scores = _validate_documents(uploaded_documents, request_type)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Document validation failed", "errors": errors, "confidence_scores": confidence_scores},
        )

    low_confidence = {k: v for k, v in confidence_scores.items() if v < 40}
    if low_confidence:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "One or more documents could not be read with sufficient confidence.",
                "errors": [f"{k.replace('_', ' ').title()}: {v}% confidence — please re-upload a clearer scan" for k, v in low_confidence.items()],
                "confidence_scores": confidence_scores,
            },
        )

    extracted = _extract_fields(uploaded_documents, declared_data)
    return {
        "ocr_extracted_data": extracted,
        "declared_prefill": extracted,
        "ocr_documents": uploaded_documents,
        "confidence_scores": confidence_scores,
        "consistency_flags": [],
        "document_freshness_passed": True,
    }


@router.post("/submit/{application_id}")
async def submit_workflow(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    app = APPLICATIONS_DB.get(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_email"] != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    if app["status"] != "draft":
        raise HTTPException(status_code=400, detail="Application already submitted")

    request_id = new_id("req")
    app["status"] = "completed"
    app["request_id"] = request_id
    WORKFLOW_DB[application_id] = {
        "status": "completed",
        "request_id": request_id,
        "rejected": False,
        "rejection_reason": None,
        "loan_prediction": {"approved": True, "probability": 0.84},
        "insurance_prediction": {"premium": 15300},
        "loan_explanation": "Income stability and credit profile support approval.",
        "insurance_explanation": "Health and lifestyle profile support moderate premium.",
    }
    WORKFLOW_EVENTS[application_id] = [
        {"agent": "kyc", "status": "complete"},
        {"agent": "onboarding", "status": "complete"},
        {"agent": "underwriting", "status": "complete"},
        {"agent": "transparency", "status": "complete"},
    ]
    return {"message": "Workflow started", "app_id": application_id, "request_id": request_id, "status": "processing"}


@router.get("/status/{application_id}")
async def get_status(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    app = APPLICATIONS_DB.get(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_email"] != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    workflow = WORKFLOW_DB.get(application_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"app_id": application_id, **workflow}


@router.get("/results/{application_id}")
async def get_results(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    app = APPLICATIONS_DB.get(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_email"] != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    workflow = WORKFLOW_DB.get(application_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "app_id": application_id,
        "request_id": workflow["request_id"],
        "loan": {
            "prediction": workflow["loan_prediction"],
            "explanation": workflow["loan_explanation"],
            "description": "Loan approved with strong affordability ratio.",
        },
        "insurance": {
            "prediction": workflow["insurance_prediction"],
            "explanation": workflow["insurance_explanation"],
            "description": "Premium estimated from age and reported health profile.",
        },
        "ocr_confidence_scores": {"bank_statement": 92.0, "aadhaar_card": 96.0},
        "model_output": {
            "loan": {"feature_contributions": {
                "credit_score": 0.38,
                "monthly_income": 0.29,
                "emi_load": -0.17,
                "loan_to_value": -0.12,
                "employment_stability": 0.21,
                "debt_to_income": -0.09,
            }},
            "insurance": {"feature_contributions": {
                "age": -0.22,
                "smoker": -0.31,
                "bmi": -0.18,
                "pre_existing_diseases": -0.14,
                "family_history": -0.08,
                "sum_insured": 0.11,
            }},
        },
        "completed": True,
    }


@router.get("/stream/{application_id}")
async def stream_workflow(application_id: str, authorization: str | None = Header(default=None)) -> StreamingResponse:
    if authorization:
        _get_email(authorization)

    async def event_generator():
        for event in WORKFLOW_EVENTS.get(application_id, []):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.2)
        yield 'data: {"done": true}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")
