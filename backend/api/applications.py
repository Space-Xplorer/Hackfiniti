from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.database import get_db
from models.user import User
from schemas.application import ApplicationCreate, ApplicationRead
from services.application_service import create_application, get_application, list_applications

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationRead])
async def list_apps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_applications(db, current_user.id)


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_app(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_application(db, current_user.id, payload.product_type)


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_app(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = await get_application(db, application_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app
