from __future__ import annotations

from typing import Any
from uuid import uuid4

USERS_DB: dict[str, dict[str, Any]] = {}
APPLICATIONS_DB: dict[str, dict[str, Any]] = {}
WORKFLOW_DB: dict[str, dict[str, Any]] = {}
WORKFLOW_EVENTS: dict[str, list[dict[str, Any]]] = {}
OTP_DB: dict[str, dict[str, Any]] = {}  # mobile -> {otp, expires_at}


def create_token(email: str) -> str:
    return f"token::{email}"


def parse_token(token: str | None) -> str | None:
    if not token or not token.startswith("token::"):
        return None
    return token.replace("token::", "", 1)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"
