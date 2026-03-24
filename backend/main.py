from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.applications import router as applications_router
from api.workflow import router as workflow_router

app = FastAPI(title="Daksha Underwriting API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,         prefix="/api/auth")
app.include_router(applications_router, prefix="/api/applications")
app.include_router(workflow_router,     prefix="/api/workflow")


@app.get("/health")
def health():
    return {"status": "ok"}