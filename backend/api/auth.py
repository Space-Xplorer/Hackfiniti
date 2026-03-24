from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .state import USERS_DB, create_token, new_id
import hashlib

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
def register(req: RegisterRequest):
    if req.email in USERS_DB:
        raise HTTPException(status_code=409, detail="User already exists")
    user = {
        "id": new_id("user"),
        "email": req.email,
        "password": hash_password(req.password),
        "name": req.name or "",
        "role": "user",
    }
    USERS_DB[req.email] = user
    return {
        "message": "User registered successfully",
        "user": {k: v for k, v in user.items() if k != "password"},
    }


@router.post("/login")
def login(req: LoginRequest):
    user = USERS_DB.get(req.email)
    if not user or user["password"] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(req.email)
    return {
        "message": "Login successful",
        "access_token": token,
        "refresh_token": token,
        "user": {k: v for k, v in user.items() if k != "password"},
    }