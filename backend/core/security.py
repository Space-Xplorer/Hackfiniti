"""
Security utilities — JWT token creation/decoding and bcrypt password hashing.

Uses python-jose for JWT and passlib[bcrypt] for password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token type constants — embed in JWT payload to distinguish access from refresh
_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


# ─────────────────────────────────────────────────────────────────────────────
# Password utilities
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*. Safe to store in DB."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* value."""
    return pwd_context.verify(plain, hashed)


# ─────────────────────────────────────────────────────────────────────────────
# JWT utilities
# ─────────────────────────────────────────────────────────────────────────────

def _make_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access JWT (default: settings.access_token_expire_minutes)."""
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _make_token(subject, _TOKEN_TYPE_ACCESS, delta)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh JWT (default: 7 days)."""
    delta = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    return _make_token(subject, _TOKEN_TYPE_REFRESH, delta)


def decode_token(token: str) -> str:
    """
    Decode and verify a JWT.

    Returns the subject (user email).
    Raises JWTError on invalid signature, expiry, or missing subject.
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    sub: str | None = payload.get("sub")
    if sub is None:
        raise JWTError("Missing subject claim")
    return sub
