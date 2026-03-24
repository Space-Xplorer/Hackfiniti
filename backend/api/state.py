import uuid
from typing import Any
from uuid import uuid4

# In-memory stores with type hints
USERS_DB: dict[str, dict[str, Any]] = {}          # email -> { id, email, password, name, role }
APPLICATIONS_DB: dict[str, dict[str, Any]] = {}   # app_id -> full application object
WORKFLOW_DB: dict[str, dict[str, Any]] = {}       # app_id -> workflow result object
WORKFLOW_EVENTS: dict[str, list[dict[str, Any]]] = {}   # app_id -> list of { agent, status }
OTP_DB: dict[str, dict[str, Any]] = {}  # mobile -> {otp, expires_at}


def create_token(email: str) -> str:
    return f"token::{email}"


def parse_token(token: str):
    """Extract email from 'token::<email>' format. Returns None if invalid."""
    if token and token.startswith("token::"):
        return token[len("token::"):]
    return None


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"