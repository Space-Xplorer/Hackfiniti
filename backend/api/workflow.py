import asyncio
import base64
import importlib
import json
import logging
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.auth_helpers import get_email_from_authorization
from api.state import APPLICATIONS_DB, WORKFLOW_DB, WORKFLOW_EVENTS, new_id

router = APIRouter(tags=["workflow"])
ocr_logger = logging.getLogger("ocr")
workflow_logger = logging.getLogger("workflow")

# Expected document types per service
REQUIRED_DOC_TYPES = {
    "loan": {"bank_statement", "salary_slip", "aadhaar_card"},
    "insurance": {"diagnostic_report", "aadhaar_card"},
    "both": {"bank_statement", "salary_slip", "diagnostic_report", "aadhaar_card"},
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

SUPPORTED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/jpg", "image/png"}

DOC_TYPE_HINTS = {
    "aadhaar_card": ["aadhaar", "aadhar", "uidai"],
    "voter_id": ["voter", "election", "epic"],
    "pan_card": ["pan", "permanent account number", "income tax"],
    "salary_slip": ["salary", "payslip", "pay slip"],
    "bank_statement": ["bank statement", "account statement"],
    "diagnostic_report": ["diagnostic", "lab report", "cholesterol", "hba1c", "blood sugar"],
}


def _detect_file_signature(raw: bytes) -> str:
    if raw.startswith(b"%PDF"):
        return "application/pdf"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "unknown"


def _extract_quick_text(raw: bytes, mime: str, name: str) -> str:
    """Best-effort text extraction for semantic doc-type validation."""
    lowered_name = (name or "").lower()
    if mime == "application/pdf" or lowered_name.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(raw))
            snippets: list[str] = []
            for page in reader.pages[:2]:
                text = page.extract_text() or ""
                if text:
                    snippets.append(text)
            return " ".join(snippets).lower()
        except Exception:
            return ""
    if mime in {"image/png", "image/jpeg", "image/jpg"} or lowered_name.endswith((".png", ".jpg", ".jpeg")):
        try:
            from PIL import Image
            import pytesseract

            image = Image.open(BytesIO(raw))
            image.load()

            # Normalize problematic PNG modes (palette/alpha/grayscale) to improve OCR stability.
            if image.mode in {"RGBA", "LA"}:
                background = Image.new("RGB", image.size, (255, 255, 255))
                alpha = image.split()[-1]
                background.paste(image, mask=alpha)
                image = background
            elif image.mode == "P":
                image = image.convert("RGB")
            elif image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")

            if image.mode == "L":
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image)
            return (text or "").lower()
        except Exception:
            return ""
    return ""


def _required_fields_for_request_type(request_type: str, uploaded_documents: list[dict]) -> list[str]:
    required_doc_types = REQUIRED_DOC_TYPES.get(request_type, set())
    uploaded_by_type = {
        (doc.get("type") or "").strip().lower(): doc
        for doc in uploaded_documents or []
        if isinstance(doc, dict)
    }

    fields: list[str] = []
    for doc_type in required_doc_types:
        if doc_type in uploaded_by_type:
            fields.extend(DOC_FIELD_MAP.get(doc_type, []))
    return sorted(set(fields))


def _compute_required_info_flags(
    extracted_data: dict,
    request_type: str,
    uploaded_documents: list[dict],
) -> dict:
    required_fields = _required_fields_for_request_type(request_type, uploaded_documents)
    missing_fields: list[str] = []

    for field in required_fields:
        value = extracted_data.get(field)
        if value is None:
            missing_fields.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing_fields.append(field)
            continue
        if isinstance(value, (list, dict)) and len(value) == 0:
            missing_fields.append(field)

    return {
        "required_fields": required_fields,
        "missing_required_fields": sorted(set(missing_fields)),
        "required_info_complete": len(missing_fields) == 0,
    }


def _infer_document_type(name: str, quick_text: str) -> str | None:
    haystack = f"{(name or '').lower()} {quick_text or ''}"
    for doc_type, hints in DOC_TYPE_HINTS.items():
        if any(hint in haystack for hint in hints):
            return doc_type
    return None


def _deterministic_confidence(size: int, mime: str, inferred: str | None, declared: str) -> float:
    score = 45.0
    score += min(35.0, size / 12000.0 * 20.0)
    if mime in SUPPORTED_MIME_TYPES:
        score += 12.0
    if inferred and inferred == declared:
        score += 8.0
    if inferred and inferred != declared:
        score -= 45.0
    return round(max(0.0, min(98.0, score)), 1)


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
        ocr_logger.warning("missing_required_docs request_type=%s missing=%s", request_type, sorted(missing))

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
        ocr_logger.info("doc_received type=%s name=%s mime=%s size_bytes=%s", doc_type, name, mime, size)

        # Reject suspiciously small files (likely random/blank)
        if size < MIN_DOC_SIZE_BYTES:
            errors.append(f"'{name}' appears to be empty or corrupt (size: {size} bytes). Please upload a valid document.")
            confidence_scores[doc_type] = 0.0
            ocr_logger.warning("doc_invalid_empty_or_corrupt type=%s name=%s size_bytes=%s", doc_type, name, size)
            continue

        file_sig = _detect_file_signature(raw)

        # MIME checks
        if mime and mime not in SUPPORTED_MIME_TYPES:
            errors.append(f"'{name}' has unsupported format '{mime}'. Use PDF, JPG, or PNG.")
            confidence_scores[doc_type] = 10.0
            ocr_logger.warning("doc_invalid_mime type=%s name=%s mime=%s", doc_type, name, mime)
            continue

        if file_sig == "unknown":
            errors.append(f"'{name}' is not a valid PDF/JPG/PNG file. Please upload a proper scan.")
            confidence_scores[doc_type] = 5.0
            ocr_logger.warning("doc_invalid_signature type=%s name=%s", doc_type, name)
            continue

        if mime and file_sig != "unknown":
            # Normalize jpg/jpeg for comparison
            norm_mime = "image/jpeg" if mime == "image/jpg" else mime
            if file_sig != norm_mime:
                errors.append(f"'{name}' file content does not match mime type '{mime}'. Re-export and upload again.")
                confidence_scores[doc_type] = 12.0
                ocr_logger.warning("doc_mime_signature_mismatch type=%s name=%s mime=%s signature=%s", doc_type, name, mime, file_sig)
                continue

        quick_text = _extract_quick_text(raw, mime or file_sig, name)
        inferred_type = _infer_document_type(name, quick_text)

        if inferred_type and inferred_type != doc_type:
            errors.append(
                f"'{name}' appears to be '{inferred_type.replace('_', ' ')}' but was uploaded as '{doc_type.replace('_', ' ')}'."
            )
            confidence_scores[doc_type] = _deterministic_confidence(size, mime or file_sig, inferred_type, doc_type)
            ocr_logger.warning(
                "doc_type_mismatch declared=%s inferred=%s name=%s",
                doc_type,
                inferred_type,
                name,
            )
            continue

        confidence_scores[doc_type] = _deterministic_confidence(size, mime or file_sig, inferred_type, doc_type)
        ocr_logger.info("doc_validated type=%s confidence=%s", doc_type, confidence_scores[doc_type])

    return errors, confidence_scores


def _extract_fields(uploaded_documents: list[dict], declared_data: dict) -> dict:
    """Simulate OCR extraction by using trustworthy declared/prefill data only."""
    extracted = dict(declared_data)
    return extracted


@router.post("/verify-kyc")
async def verify_kyc(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    get_email_from_authorization(authorization)
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
    get_email_from_authorization(authorization)

    uploaded_documents: list[dict] = payload.get("uploaded_documents") or []
    declared_data: dict = payload.get("declared_data") or {}
    request_type: str = payload.get("request_type") or "loan"
    # Pre-extracted OCR JSON from client-side Puter.js (optional)
    client_ocr: dict | None = payload.get("client_ocr")

    if not uploaded_documents and not client_ocr:
        ocr_logger.warning("preview_ocr_failed reason=no_documents")
        raise HTTPException(status_code=400, detail="No documents uploaded.")

    # --- Path A: client sent pre-extracted OCR JSON ---
    if client_ocr:
        flags, freshness_ok = _cross_validate_ocr(client_ocr)
        extracted_data = client_ocr.get("extracted_data", {})
        confidence = client_ocr.get("confidence_score", 0.0)
        ocr_status = "success" if extracted_data else "skipped"

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

        required_info = _compute_required_info_flags(prefill, request_type, uploaded_documents)

        return {
            "ocr_extracted_data": prefill,
            "declared_prefill": prefill,
            "consistency_flags": flags,
            "document_freshness_passed": freshness_ok,
            "confidence_score": confidence,
            "ocr_status": ocr_status,
            **required_info,
        }

    # --- Path B: fallback — validate raw uploaded documents ---
    errors, confidence_scores = _validate_documents(uploaded_documents, request_type)
    if errors:
        ocr_logger.warning("preview_ocr_failed reason=document_validation errors=%s", errors)
        raise HTTPException(
            status_code=422,
            detail={"message": "Document validation failed", "errors": errors, "confidence_scores": confidence_scores},
        )

    low_confidence = {k: v for k, v in confidence_scores.items() if v < 40}
    if low_confidence:
        ocr_logger.warning("preview_ocr_failed reason=low_confidence scores=%s", low_confidence)
        raise HTTPException(
            status_code=422,
            detail={
                "message": "One or more documents could not be read with sufficient confidence.",
                "errors": [f"{k.replace('_', ' ').title()}: {v}% confidence — please re-upload a clearer scan" for k, v in low_confidence.items()],
                "confidence_scores": confidence_scores,
            },
        )

    extracted = _extract_fields(uploaded_documents, declared_data)
    required_info = _compute_required_info_flags(extracted, request_type, uploaded_documents)
    ocr_logger.info("preview_ocr_success request_type=%s docs=%s", request_type, len(uploaded_documents))
    return {
        "ocr_extracted_data": extracted,
        "declared_prefill": extracted,
        "ocr_documents": uploaded_documents,
        "confidence_scores": confidence_scores,
        "consistency_flags": [],
        "document_freshness_passed": True,
        "ocr_status": "success",
        **required_info,
    }


def _agent_event(agent: str, status: str, error: str | None = None) -> dict[str, str]:
    event = {"agent": agent, "status": status}
    if error:
        event["error"] = error
    return event


def _run_kyc_step(state: dict[str, Any], events: list[dict[str, str]]) -> dict[str, Any]:
    """Delegate KYC validation to the real KYC agent (Verhoeff + PAN + name checks)."""
    try:
        import agents.kyc as kyc_module
        state = kyc_module.run(state)
        if state.get("kyc_verified"):
            events.append(_agent_event("kyc", "complete"))
            workflow_logger.info(
                "request_id=%s agent=kyc status=complete score=%.2f",
                state.get("request_id", "unknown"),
                state.get("kyc_score", 0.0),
            )
        else:
            reason = state.get("rejection_reason", "KYC validation failed")
            events.append(_agent_event("kyc", "failed", reason))
            workflow_logger.warning(
                "request_id=%s agent=kyc status=failed reason=%s mismatches=%s",
                state.get("request_id", "unknown"),
                reason,
                state.get("kyc_mismatches", []),
            )
    except Exception as exc:
        state["kyc_verified"] = False
        state["rejected"] = True
        state["rejection_reason"] = f"KYC system error: {exc}"
        state.setdefault("errors", []).append(str(exc))
        events.append(_agent_event("kyc", "failed", str(exc)))
        workflow_logger.error("request_id=%s agent=kyc status=error exc=%s",
                              state.get("request_id", "unknown"), exc)
    return state


def _run_agent_step(
    state: dict[str, Any],
    events: list[dict[str, str]],
    *,
    agent_name: str,
    module_name: str,
    class_name: str,
    method_name: str,
) -> dict[str, Any]:
    request_id = state.get("request_id", "unknown")
    try:
        module = importlib.import_module(module_name)
        agent_cls = getattr(module, class_name)
        method = getattr(agent_cls(), method_name)
        updated = method(state)
        if isinstance(updated, dict):
            state = updated
        events.append(_agent_event(agent_name, "complete"))
        workflow_logger.info(
            "request_id=%s agent=%s status=complete keys=%s",
            request_id,
            agent_name,
            sorted(list(state.keys())),
        )
    except Exception as exc:
        message = f"{agent_name} failed: {exc}"
        state.setdefault("errors", []).append(message)
        workflow_logger.warning(message)
        events.append(_agent_event(agent_name, "failed", str(exc)))
    return state


def _run_underwriting_step(state: dict[str, Any], events: list[dict[str, str]]) -> dict[str, Any]:
    try:
        module = importlib.import_module("agents.underwriting")
        agent = getattr(module, "UnderwritingAgent")()
        request_type = state.get("request_type")

        if request_type in ["loan", "both"]:
            state = agent.process_loan(state)
        if request_type in ["insurance", "both", "health"]:
            state = agent.process_insurance(state)

        events.append(_agent_event("underwriting", "complete"))
        workflow_logger.info(
            "request_id=%s agent=underwriting status=complete loan_prediction=%s insurance_prediction=%s",
            state.get("request_id", "unknown"),
            bool(state.get("loan_prediction")),
            bool(state.get("insurance_prediction")),
        )
    except Exception as exc:
        message = f"underwriting failed: {exc}"
        state.setdefault("errors", []).append(message)
        workflow_logger.warning(message)
        events.append(_agent_event("underwriting", "failed", str(exc)))
    return state


def _run_transparency_step(state: dict[str, Any], events: list[dict[str, str]]) -> dict[str, Any]:
    try:
        module = importlib.import_module("agents.transparency")
        agent = getattr(module, "TransparencyAgent")()
        request_type = state.get("request_type")

        if request_type in ["loan", "both"] and state.get("loan_prediction"):
            state = agent.explain_loan_decision(state)
        if request_type in ["insurance", "both", "health"] and state.get("insurance_prediction"):
            state = agent.explain_insurance_premium(state)

        events.append(_agent_event("transparency", "complete"))
        workflow_logger.info(
            "request_id=%s agent=transparency status=complete loan_explanation=%s insurance_explanation=%s",
            state.get("request_id", "unknown"),
            bool(state.get("loan_explanation")),
            bool(state.get("insurance_explanation")),
        )
    except Exception as exc:
        message = f"transparency failed: {exc}"
        state.setdefault("errors", []).append(message)
        workflow_logger.warning(message)
        events.append(_agent_event("transparency", "failed", str(exc)))
    return state


def _build_agent_state(application_id: str, request_id: str, app: dict[str, Any]) -> dict[str, Any]:
    declared = dict(app.get("applicant_data") or {})
    return {
        "application_id": application_id,
        "request_id": request_id,
        "request_type": app.get("request_type", "loan"),
        "loan_type": app.get("loan_type"),
        "declared_data": declared,
        "applicant_data": declared,
        "uploaded_documents": app.get("uploaded_documents") or [],
        "submitted_name": app.get("submitted_name") or "",
        "submitted_dob": app.get("submitted_dob") or "",
        "submitted_aadhaar": app.get("submitted_aadhaar") or "",
        "errors": [],
        "rejected": False,
        "completed": False,
    }


def _run_agent_pipeline(application_id: str, request_id: str, app: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    state = _build_agent_state(application_id, request_id, app)
    events: list[dict[str, str]] = []

    state = _run_kyc_step(state, events)
    if not state.get("kyc_verified"):
        state["completed"] = True
        return state, events

    state = _run_agent_step(state, events, agent_name="onboarding", module_name="agents.onboarding", class_name="OnboardingAgent", method_name="process_documents")
    state = _run_agent_step(state, events, agent_name="fraud", module_name="agents.fraud", class_name="FraudAgent", method_name="check_fraud")
    state = _run_agent_step(state, events, agent_name="feature_engineering", module_name="agents.feature_engineering", class_name="FeatureEngineeringAgent", method_name="process")
    state = _run_agent_step(state, events, agent_name="compliance", module_name="agents.compliance", class_name="ComplianceAgent", method_name="check_compliance")
    state = _run_underwriting_step(state, events)
    state = _run_agent_step(state, events, agent_name="verification", module_name="agents.verification", class_name="VerificationAgent", method_name="verify_decision")
    state = _run_transparency_step(state, events)
    state = _run_agent_step(state, events, agent_name="supervisor", module_name="agents.supervisor", class_name="SupervisorAgent", method_name="make_decision")

    state["completed"] = True
    return state, events


def _merge_agent_outputs(application_id: str, app: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    rejected = bool(state.get("rejected", False))
    merged: dict[str, Any] = {} if rejected else _compute_results(application_id, app)

    if state.get("loan_prediction"):
        merged["loan_prediction"] = state["loan_prediction"]
    if state.get("insurance_prediction"):
        merged["insurance_prediction"] = state["insurance_prediction"]
    if state.get("loan_explanation"):
        merged["loan_explanation"] = state["loan_explanation"]
    if state.get("insurance_explanation"):
        merged["insurance_explanation"] = state["insurance_explanation"]
    if state.get("model_output"):
        merged["model_output"] = state["model_output"]

    verification = state.get("loan_verification") or state.get("insurance_verification")
    if verification:
        merged["verification_result"] = verification

    if state.get("ocr_confidence_scores"):
        merged["ocr_confidence_scores"] = state["ocr_confidence_scores"]

    document_verification = state.get("document_verification") or {}
    stale_docs = [k for k, v in document_verification.items() if isinstance(v, dict) and not v.get("is_fresh", True)]
    if stale_docs:
        merged["ocr_freshness_warnings"] = [f"{doc} may be stale" for doc in stale_docs]

    if rejected:
        merged.setdefault("verification_result", {
            "verified": False,
            "concerns": [state.get("rejection_reason") or "Application rejected"],
            "recommendation": "REJECT",
        })
        merged.setdefault("ocr_confidence_scores", {})
        merged.setdefault("ocr_freshness_warnings", [])

    return merged


@router.post("/submit/{application_id}")
async def submit_workflow(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = get_email_from_authorization(authorization)
    app = APPLICATIONS_DB.get(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_email"] != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    if app["status"] != "draft":
        raise HTTPException(status_code=400, detail="Application already submitted")

    request_id = new_id("req")
    app["status"] = "submitted"
    app["request_id"] = request_id

    # Run the synchronous agent pipeline off the event loop thread so we don't
    # block uvicorn's async worker during LLM calls (which can take 5-30s).
    loop = asyncio.get_event_loop()
    import functools
    final_state, events = await loop.run_in_executor(
        None,
        functools.partial(_run_agent_pipeline, application_id, request_id, app),
    )
    results = _merge_agent_outputs(application_id, app, final_state)

    workflow_status = "completed" if final_state.get("completed") else "failed"
    WORKFLOW_DB[application_id] = {
        "status": workflow_status,
        "request_id": request_id,
        "rejected": bool(final_state.get("rejected", False)),
        "rejection_reason": final_state.get("rejection_reason"),
        "agent_errors": final_state.get("errors", []),
        **results,
    }
    WORKFLOW_EVENTS[application_id] = events
    app["status"] = "completed" if workflow_status == "completed" else "failed"

    workflow_logger.info(
        "request_id=%s app_id=%s workflow_status=%s rejected=%s rejection_reason=%s agent_errors=%s",
        request_id,
        application_id,
        workflow_status,
        bool(final_state.get("rejected", False)),
        final_state.get("rejection_reason"),
        final_state.get("errors", []),
    )

    return {"message": "Workflow started", "app_id": application_id, "request_id": request_id, "status": "processing"}






@router.get("/status/{application_id}")
async def get_status(application_id: str, authorization: str | None = Header(default=None)) -> dict:
    user_email = get_email_from_authorization(authorization)
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
    user_email = get_email_from_authorization(authorization)
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
async def stream_workflow(
    application_id: str,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> StreamingResponse:
    if authorization:
        get_email_from_authorization(authorization)
    elif token:
        get_email_from_authorization(f"Bearer {token}")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    async def event_generator():
        for event in WORKFLOW_EVENTS.get(application_id, []):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.2)
        yield 'data: {"done": true}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")