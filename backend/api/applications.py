from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from .state import APPLICATIONS_DB, parse_token, new_id

router = APIRouter()


def get_email(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "").strip()
    email = parse_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return email


class DocumentInput(BaseModel):
    type: str
    name: str
    mime_type: str
    content_base64: str


class CreateApplicationRequest(BaseModel):
    request_type: str                          # "loan" | "insurance"
    loan_type: Optional[str] = None            # "home" | "personal" | None
    submitted_name: Optional[str] = ""
    submitted_dob: Optional[str] = ""
    submitted_aadhaar: Optional[str] = ""
    applicant_data: Optional[Dict[str, Any]] = {}
    uploaded_documents: Optional[List[DocumentInput]] = []


@router.post("/")
def create_application(req: CreateApplicationRequest, authorization: str = Header(...)):
    email = get_email(authorization)
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
        "uploaded_documents": [d.dict() for d in req.uploaded_documents],
    }
    APPLICATIONS_DB[app_id] = app
    return {"message": "Application created", "application": app}


@router.get("/")
def list_applications(authorization: str = Header(...)):
    email = get_email(authorization)
    items = [app for app in APPLICATIONS_DB.values() if app["user_email"] == email]
    return {"items": items}