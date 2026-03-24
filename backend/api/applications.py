from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from api.state import APPLICATIONS_DB, new_id, parse_token

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreatePayload(BaseModel):
    request_type: str
    loan_type: str | None = None
    submitted_name: str | None = None
    submitted_dob: str | None = None
    submitted_aadhaar: str | None = None
    applicant_data: dict = {}
    uploaded_documents: list[dict] = []


def _get_email(authorization: str | None) -> str:
    token = (authorization or "").replace("Bearer ", "", 1)
    email = parse_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return email


@router.post("/")
async def create_application(payload: ApplicationCreatePayload, authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    app_id = new_id("app")
    APPLICATIONS_DB[app_id] = {
        "id": app_id,
        "user_email": user_email,
        "status": "draft",
        "request_type": payload.request_type,
        "loan_type": payload.loan_type,
        "submitted_name": payload.submitted_name,
        "submitted_dob": payload.submitted_dob,
        "submitted_aadhaar": payload.submitted_aadhaar,
        "applicant_data": payload.applicant_data,
        "uploaded_documents": payload.uploaded_documents,
    }
    return {"message": "Application created", "application": APPLICATIONS_DB[app_id]}


@router.get("")
async def list_applications(authorization: str | None = Header(default=None)) -> dict:
    user_email = _get_email(authorization)
    items = [app for app in APPLICATIONS_DB.values() if app["user_email"] == user_email]
    return {"items": items}
