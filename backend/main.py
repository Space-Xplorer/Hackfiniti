import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.ocr_logging import configure_ocr_logger
from core.workflow_logging import configure_workflow_logger
from api.applications import router as applications_router
from api.auth import router as auth_router
from api.workflow import router as workflow_router

configure_ocr_logger()
configure_workflow_logger()

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)