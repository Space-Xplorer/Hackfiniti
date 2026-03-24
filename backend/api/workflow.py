import asyncio
import json

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from api.state import APPLICATIONS_DB, WORKFLOW_DB, WORKFLOW_EVENTS, new_id, parse_token

router = APIRouter(prefix="/workflow", tags=["workflow"])


def _get_email(authorization: str | None) -> str:
    token = (authorization or "").replace("Bearer ", "", 1)
    email = parse_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return email


@router.post("/verify-kyc")
async def verify_kyc(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    _get_email(authorization)
    if not payload.get("name") or not payload.get("aadhaar"):
        raise HTTPException(status_code=400, detail="Name and Aadhaar are required")
    return {
        "verified": True,
        "kyc_data": {
            "name": payload.get("name"),
            "aadhaar_number": payload.get("aadhaar"),
            "dob": payload.get("dob"),
            "cibil_score": 742,
            "gender": "Male",
            "address": "Mock Address",
        },
    }


@router.post("/preview-ocr")
async def preview_ocr(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    _get_email(authorization)
    declared = payload.get("declared_data") or {}
    prefill = dict(declared)
    prefill.setdefault("age", 31)
    prefill.setdefault("gender", "Male")
    prefill.setdefault("declared_monthly_income", 95000)
    return {"ocr_extracted_data": prefill, "declared_prefill": prefill, "ocr_documents": payload.get("uploaded_documents", [])}


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
            "loan": {"feature_contributions": {"credit_score": 0.38, "income": 0.29, "emi_load": -0.17}},
            "insurance": {"feature_contributions": {"age": 0.22, "smoker": -0.18, "weight": -0.11}},
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
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
