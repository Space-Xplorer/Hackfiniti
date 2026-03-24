from fastapi import APIRouter

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/submit")
async def submit_workflow() -> dict:
    return {"status": "submitted"}


@router.get("/status/{application_id}")
async def get_status(application_id: int) -> dict:
    return {"application_id": application_id, "status": "pending"}


@router.get("/results/{application_id}")
async def get_results(application_id: int) -> dict:
    return {"application_id": application_id, "result": None}
