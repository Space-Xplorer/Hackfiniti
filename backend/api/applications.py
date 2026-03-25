from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Dict

from .auth_helpers import get_email_from_authorization
from .state import APPLICATIONS_DB, new_id

router = APIRouter()

_VALID_REQUEST_TYPES = {"loan", "insurance", "both"}
_VALID_LOAN_TYPES = {"home", "personal", "business", None}


class DocumentInput(BaseModel):
    type: str
    name: str
    mime_type: str
    content_base64: str


class CreateApplicationRequest(BaseModel):
    request_type: str = Field(..., description="'loan' | 'insurance' | 'both'")
    loan_type: Optional[str] = Field(None, description="'home' | 'personal' | 'business' | null")
    submitted_name: Optional[str] = ""
    submitted_dob: Optional[str] = ""
    submitted_aadhaar: Optional[str] = ""
    applicant_data: Optional[Dict[str, Any]] = {}
    uploaded_documents: Optional[List[DocumentInput]] = []

    @field_validator("request_type")
    @classmethod
    def validate_request_type(cls, v: str) -> str:
        if v not in _VALID_REQUEST_TYPES:
            raise ValueError(f"request_type must be one of {sorted(_VALID_REQUEST_TYPES)}")
        return v

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_LOAN_TYPES:
            raise ValueError(f"loan_type must be one of {sorted(t for t in _VALID_LOAN_TYPES if t)}")
        return v

    @field_validator("applicant_data")
    @classmethod
    def validate_applicant_data(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        data = v or {}

        # Loan amount — RBI: min ₹10,000 / max ₹10 Cr
        if "loan_amount_requested" in data:
            amt = float(data["loan_amount_requested"])
            if not (10_000 <= amt <= 100_000_000):
                raise ValueError("loan_amount_requested must be between ₹10,000 and ₹10,00,00,000")

        # CIBIL / credit score — CRIF scale 300-900
        if "credit_score" in data or "cibil_score" in data:
            score = int(data.get("credit_score") or data.get("cibil_score"))
            if not (300 <= score <= 900):
                raise ValueError("cibil_score must be between 300 and 900")

        # Age — IRDAI & RBI: 18-80
        if "age" in data:
            age = int(data["age"])
            if not (18 <= age <= 80):
                raise ValueError("age must be between 18 and 80")

        # Monthly income — positive, cap at 10 Cr/month
        if "declared_monthly_income" in data:
            income = float(data["declared_monthly_income"])
            if income <= 0 or income > 10_000_000:
                raise ValueError("declared_monthly_income must be > 0 and ≤ ₹1,00,00,000")

        # BMI — human physiological range
        if "bmi" in data:
            bmi = float(data["bmi"])
            if not (10 <= bmi <= 60):
                raise ValueError("bmi must be between 10 and 60")

        return data

    @field_validator("submitted_aadhaar")
    @classmethod
    def validate_aadhaar_format(cls, v: Optional[str]) -> Optional[str]:
        """Basic format check — full Verhoeff checksum is done in the KYC agent."""
        if v and not v.replace(" ", "").isdigit():
            raise ValueError("submitted_aadhaar must contain only digits")
        return v


@router.post("/")
def create_application(req: CreateApplicationRequest, authorization: str = Header(...)):
    email = get_email_from_authorization(authorization)
    app_id = new_id("app")
    app = {
        "id": app_id,
        "user_email": email,
        "status": "draft",
        "request_type": req.request_type,
        "loan_type": req.loan_type,
        "submitted_name": req.submitted_name,
        "submitted_dob": req.submitted_dob,
        "submitted_aadhaar": req.submitted_aadhaar,
        "applicant_data": req.applicant_data or {},
        "uploaded_documents": [d.model_dump() for d in (req.uploaded_documents or [])],
    }
    APPLICATIONS_DB[app_id] = app
    return {"message": "Application created", "application": app}


@router.get("/")
def list_applications(authorization: str = Header(...)):
    email = get_email_from_authorization(authorization)
    items = [app for app in APPLICATIONS_DB.values() if app["user_email"] == email]
    return {"items": items}