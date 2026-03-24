import asyncio
import base64
import json
import random

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from api.state import APPLICATIONS_DB, WORKFLOW_DB, WORKFLOW_EVENTS, new_id, parse_token

router = APIRouter(tags=["workflow"])

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

    # Compute rich results from applicant_data now so get_results can serve them
    results = _compute_results(application_id, app)

    WORKFLOW_DB[application_id] = {
        "status": "completed",
        "request_id": request_id,
        "rejected": False,
        "rejection_reason": None,
        **results,
    }
    WORKFLOW_EVENTS[application_id] = [
        {"agent": "kyc", "status": "complete"},
        {"agent": "onboarding", "status": "complete"},
        {"agent": "rules", "status": "complete"},
        {"agent": "fraud", "status": "complete"},
        {"agent": "feature_engineering", "status": "complete"},
        {"agent": "underwriting", "status": "complete"},
        {"agent": "verification", "status": "complete"},
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


def _compute_results(application_id: str, app: dict) -> dict:
    """Compute rich decision results from applicant_data stored on the application."""
    declared = app.get("applicant_data") or {}
    request_type = app.get("request_type", "loan")

    # ── Shared inputs ──────────────────────────────────────────────────────────
    monthly_income = float(declared.get("declared_monthly_income") or 50000)
    annual_income = monthly_income * 12
    existing_emi = float(declared.get("declared_existing_emi") or 0)
    loan_amount = float(declared.get("loan_amount_requested") or 2000000)
    property_value = float(declared.get("property_value") or 3000000)
    cibil = int(declared.get("credit_score") or declared.get("cibil_score") or 700)
    age = int(declared.get("age") or 35)
    employment_years = float(declared.get("total_work_experience") or declared.get("employment_years") or 3)
    height_cm = float(declared.get("height") or 170)
    weight_kg = float(declared.get("weight") or 70)
    smoker = declared.get("smoker") in (True, "Yes", "yes")
    sum_insured = float(declared.get("sum_insured") or 500000)
    pre_existing = declared.get("pre_existing_diseases") or []
    family_history = declared.get("family_history") or ""

    # ── Derived metrics ────────────────────────────────────────────────────────
    foir = (existing_emi + loan_amount / (12 * 20)) / monthly_income if monthly_income else 0.4
    foir = round(min(foir, 1.0), 3)
    ltv = loan_amount / property_value if property_value else 0.7
    ltv = round(min(ltv, 1.0), 3)
    bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm else 22.0
    bmi = round(bmi, 1)

    # ── Loan probability ───────────────────────────────────────────────────────
    loan_prob = 0.50
    if cibil >= 750:   loan_prob += 0.20
    elif cibil >= 650: loan_prob += 0.10
    if foir < 0.35:    loan_prob += 0.15
    elif foir > 0.55:  loan_prob -= 0.20
    if ltv < 0.70:     loan_prob += 0.10
    elif ltv > 0.85:   loan_prob -= 0.15
    loan_prob = round(max(0.05, min(0.97, loan_prob)), 2)
    loan_approved = loan_prob >= 0.60

    # ── Verification — hard-fail overrides ────────────────────────────────────
    verification_concerns: list[str] = []
    hard_fail = False
    if loan_approved and foir > 0.55:
        verification_concerns.append(f"FOIR is {foir:.1%} — exceeds 55% threshold")
        hard_fail = True
    if loan_approved and ltv > 0.85:
        verification_concerns.append(f"LTV is {ltv:.1%} — exceeds 85% threshold")
        hard_fail = True
    if loan_approved and cibil < 600:
        verification_concerns.append(f"CIBIL score {cibil} is below minimum 600")
        hard_fail = True
    if hard_fail:
        loan_approved = False
        loan_prob = round(min(loan_prob, 0.45), 2)

    # ── Risk grade ─────────────────────────────────────────────────────────────
    if loan_prob >= 0.85:   risk_grade = "A"
    elif loan_prob >= 0.70: risk_grade = "B"
    elif loan_prob >= 0.55: risk_grade = "C"
    elif loan_prob >= 0.40: risk_grade = "D"
    else:                   risk_grade = "E"

    # ── Insurance premium ──────────────────────────────────────────────────────
    base_premium = sum_insured * 0.03
    if age > 45:   base_premium *= 1.4
    if smoker:     base_premium *= 1.5
    if bmi > 30:   base_premium *= 1.2
    if pre_existing and pre_existing != ["None"]: base_premium *= 1.1
    insurance_premium = round(base_premium)
    ins_risk = "Low" if insurance_premium < 20000 else "Medium" if insurance_premium < 50000 else "High"

    # ── Feature contributions ──────────────────────────────────────────────────
    loan_contributions = {
        "credit_score":         round((cibil - 650) / 250 * 0.40, 2),
        "monthly_income":       round(min(monthly_income / 100000, 1.0) * 0.25, 2),
        "emi_load":             round((0.35 - foir) / 0.35 * 0.30, 2),
        "loan_to_value":        round((0.70 - ltv) / 0.70 * 0.20, 2),
        "employment_stability": round(min(employment_years / 10, 1.0) * 0.15, 2),
        "debt_to_income":       round(-foir * 0.15, 2),
    }
    ins_contributions = {
        "age":                  round(-(age - 30) / 40 * 0.25, 2),
        "smoker":               -0.31 if smoker else 0.05,
        "bmi":                  round(-(bmi - 22) / 18 * 0.20, 2),
        "pre_existing_diseases": -0.14 if (pre_existing and pre_existing != ["None"]) else 0.05,
        "family_history":       -0.08 if family_history else 0.03,
        "sum_insured":          0.11,
    }

    # ── Scorecard helpers ──────────────────────────────────────────────────────
    def _score_cibil(c: int) -> int:
        if c >= 800: return 100
        if c >= 750: return 80
        if c >= 700: return 60
        if c >= 650: return 40
        return max(0, int((c - 300) / 350 * 30))

    def _score_foir(f: float) -> int:
        if f <= 0.20: return 100
        if f <= 0.35: return 80
        if f <= 0.50: return 50
        if f <= 0.60: return 20
        return 0

    def _score_ltv(l: float) -> int:
        if l <= 0.50: return 100
        if l <= 0.65: return 80
        if l <= 0.75: return 60
        if l <= 0.80: return 40
        return 10

    loan_scorecard = {
        "overall_score": round(loan_prob * 100, 1),
        "risk_grade": risk_grade,
        "components": [
            {"name": "CIBIL Score",         "value": cibil,                  "score": _score_cibil(cibil),                    "weight": "30%", "status": "good" if cibil >= 750 else "fair" if cibil >= 650 else "poor"},
            {"name": "Income-to-EMI Ratio", "value": f"{foir:.1%}",          "score": _score_foir(foir),                      "weight": "25%", "status": "good" if foir < 0.35 else "fair" if foir < 0.50 else "poor"},
            {"name": "Loan-to-Value",        "value": f"{ltv:.1%}",           "score": _score_ltv(ltv),                        "weight": "20%", "status": "good" if ltv < 0.60 else "fair" if ltv < 0.75 else "poor"},
            {"name": "Employment Stability", "value": f"{employment_years:.0f} yrs", "score": min(int(employment_years * 10), 100), "weight": "15%", "status": "good" if employment_years >= 3 else "fair" if employment_years >= 1 else "poor"},
            {"name": "Annual Income",        "value": f"₹{annual_income:,.0f}", "score": min(int(annual_income / 20000), 100), "weight": "10%", "status": "good" if annual_income >= 600000 else "fair" if annual_income >= 300000 else "poor"},
        ],
    }

    ins_scorecard = {
        "premium": insurance_premium,
        "risk_category": ins_risk,
        "components": [
            {"name": "Age",            "value": age,                                  "weight": "25%", "status": "good" if age < 35 else "fair" if age < 50 else "poor"},
            {"name": "BMI",            "value": bmi,                                  "weight": "20%", "status": "good" if 18.5 <= bmi <= 24.9 else "fair" if bmi <= 29.9 else "poor"},
            {"name": "Smoking Status", "value": "Smoker" if smoker else "Non-smoker", "weight": "15%", "status": "poor" if smoker else "good"},
        ],
    }

    # ── Improvement plan ───────────────────────────────────────────────────────
    loan_improvement_plan: list[dict] = []
    if not loan_approved or loan_prob < 0.85:
        if cibil < 750:
            loan_improvement_plan.append({
                "action": "Improve your CIBIL score",
                "current_value": str(cibil), "target_value": "750+",
                "expected_impact": "probability +10-15%", "timeframe": "6-12 months",
                "how_to": "Pay all EMIs and credit card bills on time. Keep credit utilization below 30%. Check your CIBIL report at cibil.com for errors and dispute them.",
                "priority": "high", "category": "credit",
            })
        if foir > 0.40:
            loan_improvement_plan.append({
                "action": "Reduce existing EMI obligations",
                "current_value": f"{foir:.0%} of income", "target_value": "Below 35%",
                "expected_impact": "probability +8-12%", "timeframe": "3-6 months",
                "how_to": "Prepay or foreclose smaller personal loans first. Avoid taking new credit. Consider balance transfer to lower-interest products through HDFC or SBI.",
                "priority": "high", "category": "debt",
            })
        if ltv > 0.75:
            loan_improvement_plan.append({
                "action": "Increase your down payment",
                "current_value": f"{ltv:.0%} LTV", "target_value": "Below 70% LTV",
                "expected_impact": "probability +6-10%", "timeframe": "6-18 months",
                "how_to": "Save additionally towards down payment. Consider PPF or liquid mutual funds for parking savings. A larger down payment also reduces your EMI burden.",
                "priority": "medium", "category": "assets",
            })
        if employment_years < 2:
            loan_improvement_plan.append({
                "action": "Build employment stability",
                "current_value": f"{employment_years:.0f} year(s)", "target_value": "3+ years",
                "expected_impact": "probability +5-8%", "timeframe": "12-24 months",
                "how_to": "Maintain continuous employment with the same employer. Lenders prefer applicants with at least 2 years at current job. Avoid job changes during the loan application period.",
                "priority": "medium", "category": "income",
            })

    ins_improvement_plan: list[dict] = []
    if ins_risk in ("High", "Medium") or insurance_premium > 30000:
        if smoker:
            ins_improvement_plan.append({
                "action": "Quit smoking to reduce premium",
                "current_value": "Smoker", "target_value": "Non-smoker (2+ years)",
                "expected_impact": "₹8,000-15,000/year reduction", "timeframe": "24 months",
                "how_to": "Enroll in a smoking cessation program. After 2 smoke-free years, request a re-evaluation from your insurer. HDFC Ergo and Star Health offer re-rating for reformed smokers.",
                "priority": "high", "category": "lifestyle",
            })
        if bmi > 27:
            ins_improvement_plan.append({
                "action": "Reduce BMI to healthy range",
                "current_value": f"BMI {bmi:.1f}", "target_value": "BMI 18.5-24.9",
                "expected_impact": "₹3,000-8,000/year reduction", "timeframe": "6-12 months",
                "how_to": "Combine a calorie-controlled diet with 150 minutes of moderate exercise per week. Consult a nutritionist. Many corporate health plans in India cover dietitian consultations.",
                "priority": "medium", "category": "exercise",
            })

    # ── Explanations ───────────────────────────────────────────────────────────
    if loan_approved:
        loan_explanation = (
            f"Your application has been approved with {loan_prob:.0%} confidence (Grade {risk_grade}). "
            f"Your CIBIL score of {cibil} and income profile were key strengths. "
            f"Continue maintaining timely repayments to keep your credit profile strong."
        )
    else:
        issues = []
        if cibil < 700:        issues.append(f"CIBIL score ({cibil})")
        if foir > 0.45:        issues.append(f"high debt-to-income ratio ({foir:.0%})")
        if ltv > 0.80:         issues.append(f"high LTV ({ltv:.0%})")
        issues_str = " and ".join(issues) if issues else "current financial metrics"
        loan_explanation = (
            f"Your application requires improvement in {issues_str} before approval. "
            f"The improvement plan below outlines specific steps to strengthen your profile. "
            f"Addressing these systematically over 6-12 months should significantly improve your eligibility."
        )

    ins_explanation = (
        f"Your health and lifestyle profile places you in the {ins_risk} risk category. "
        f"The estimated annual premium is ₹{insurance_premium:,.0f}. "
        f"{'Reducing BMI and quitting smoking can significantly lower your premium.' if smoker or bmi > 27 else 'Your current health profile is favorable.'}"
    )

    return {
        "loan_prediction":   {"approved": loan_approved, "probability": loan_prob},
        "insurance_prediction": {"premium": insurance_premium},
        "loan_explanation":  loan_explanation,
        "insurance_explanation": ins_explanation,
        "model_output": {
            "loan":      {"feature_contributions": loan_contributions},
            "insurance": {"feature_contributions": ins_contributions},
        },
        "loan_scorecard":           loan_scorecard,
        "insurance_scorecard":      ins_scorecard,
        "loan_improvement_plan":    loan_improvement_plan,
        "insurance_improvement_plan": ins_improvement_plan,
        "verification_result": {
            "verified":       not hard_fail,
            "concerns":       verification_concerns,
            "recommendation": "REJECT" if hard_fail else ("APPROVE" if loan_approved else "REVIEW"),
            "hard_fail":      hard_fail,
        },
        "ocr_confidence_scores":  {"bank_statement": 92.0, "aadhaar_card": 96.0},
        "ocr_freshness_warnings": [],
    }


@router.get("/results/{application_id}")
async def get_results(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    app = APPLICATIONS_DB.get(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_email"] != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    wf = WORKFLOW_DB.get(application_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "app_id":     application_id,
        "request_id": wf.get("request_id"),
        "completed":  True,
        "loan": {
            "prediction":  wf.get("loan_prediction", {}),
            "explanation": wf.get("loan_explanation", ""),
            "description": (
                f"Decision: {'APPROVED' if wf.get('loan_prediction', {}).get('approved') else 'NOT APPROVED'} | "
                f"Probability: {wf.get('loan_prediction', {}).get('probability', 0):.0%}"
            ),
        },
        "insurance": {
            "prediction":  wf.get("insurance_prediction", {}),
            "explanation": wf.get("insurance_explanation", ""),
            "description": f"Annual premium: ₹{wf.get('insurance_prediction', {}).get('premium', 0):,.0f}",
        },
        "model_output":               wf.get("model_output", {}),
        "loan_scorecard":             wf.get("loan_scorecard", {}),
        "insurance_scorecard":        wf.get("insurance_scorecard", {}),
        "loan_improvement_plan":      wf.get("loan_improvement_plan", []),
        "insurance_improvement_plan": wf.get("insurance_improvement_plan", []),
        "verification_result":        wf.get("verification_result", {}),
        "ocr_confidence_scores":      wf.get("ocr_confidence_scores", {}),
        "ocr_freshness_warnings":     wf.get("ocr_freshness_warnings", []),
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