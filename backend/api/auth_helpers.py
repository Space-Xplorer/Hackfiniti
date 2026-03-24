from fastapi import HTTPException

from .state import parse_token


def get_email_from_authorization(authorization: str | None) -> str:
    token = (authorization or "").replace("Bearer ", "", 1).strip()
    email = parse_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return email
