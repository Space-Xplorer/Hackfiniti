from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.applications import router as applications_router
from api.workflow import router as workflow_router
from core.database import engine
from models.user import Base as UserBase
from models.application import Application  # noqa: F401 – ensures table is registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
    yield


app = FastAPI(title="Niyati API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
