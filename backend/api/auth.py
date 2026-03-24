from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.state import USERS_DB, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginPayload(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(payload: RegisterPayload) -> dict:
    email = payload.email.lower().strip()
    if email in USERS_DB:
        raise HTTPException(status_code=409, detail="User already exists")
    USERS_DB[email] = {
        "id": str(len(USERS_DB) + 1),
        "email": email,
        "password": payload.password,
        "name": payload.name or email.split("@")[0],
        "role": "user",
    }
    user = USERS_DB[email]
    return {"message": "User registered successfully", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}}


@router.post("/login")
async def login(payload: LoginPayload) -> dict:
    email = payload.email.lower().strip()
    user = USERS_DB.get(email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(email)
    return {
        "message": "Login successful",
        "access_token": token,
        "refresh_token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]},
    }
