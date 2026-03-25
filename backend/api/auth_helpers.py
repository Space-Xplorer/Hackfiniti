from fastapi import HTTPException
from jose import JWTError

from core.security import decode_token


def get_email_from_authorization(authorization: str | None) -> str:
    """
    Extract and cryptographically verify the caller's email from an Authorization header.

    Raises HTTP 401 if the header is missing, malformed, or the JWT signature is invalid / expired.
    """
    raw_token = (authorization or "").strip()
    if raw_token.lower().startswith("bearer "):
        raw_token = raw_token[7:].strip()

    if not raw_token:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        email = decode_token(raw_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}") from exc

    if not email:
        raise HTTPException(status_code=401, detail="Token subject missing")

    return email
