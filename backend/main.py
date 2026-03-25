"""
FastAPI application entry point.

Security & production hardening applied here:
  - CORS origins driven by CORS_ORIGINS env var (not hardcoded "*")
  - Rate limiting via slowapi on auth routes (disabled in TEST_MODE)
  - X-Request-ID correlation middleware for structured log tracing
"""

import logging
import os
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.config import settings
from core.ocr_logging import configure_ocr_logger
from core.workflow_logging import configure_workflow_logger
from api.applications import router as applications_router
from api.auth import router as auth_router
from api.workflow import router as workflow_router

configure_ocr_logger()
configure_workflow_logger()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# ─── Rate limiter ─────────────────────────────────────────────────────────────
from core.limiter import limiter

app = FastAPI(title="Daksha Underwriting API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SlowAPIMiddleware MUST be added before CORS middleware so it populates
# request.state.view_rate_limit before the rate-limited route handler runs.
app.add_middleware(SlowAPIMiddleware)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Set CORS_ORIGINS=https://daksha.yourdomain.com in .env for production.
# Multiple origins can be comma-separated.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Correlation ID middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_correlation_id(request: Request, call_next) -> Response:
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


app.include_router(auth_router,         prefix="/api/auth")
app.include_router(applications_router, prefix="/api/applications")
app.include_router(workflow_router,     prefix="/api/workflow")

# ─── Prometheus Metrics ────────────────────────────────────────────────────────
# Exposes /metrics endpoint for Prometheus scrapers
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)