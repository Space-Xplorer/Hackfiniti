from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.workflow import WorkflowSubmitRequest, WorkflowStatusResponse
from services.application_service import get_application
from services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])
_service = WorkflowService()


@router.post("/submit", response_model=WorkflowStatusResponse)
async def submit_workflow(
    payload: WorkflowSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await get_application(db, payload.application_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    result = await _service.run(payload.application_id)
    return result


@router.get("/status/{application_id}", response_model=WorkflowStatusResponse)
async def get_status(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await get_application(db, application_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"application_id": application_id, "status": app.status}


@router.get("/results/{application_id}")
async def get_results(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await get_application(db, application_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"application_id": application_id, "status": app.status, "result": None}
