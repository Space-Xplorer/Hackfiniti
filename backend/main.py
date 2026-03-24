from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.applications import router as applications_router
from api.auth import router as auth_router
from api.workflow import router as workflow_router

app = FastAPI(title="Daksha API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(workflow_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
