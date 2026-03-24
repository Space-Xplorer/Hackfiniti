from fastapi import APIRouter

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("")
async def list_applications() -> dict:
    return {"items": []}
