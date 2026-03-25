"""
Authentication router — uses real JWT (python-jose) + bcrypt (passlib) via core/security.py.

Security improvements over previous version:
  - Passwords hashed with bcrypt (was SHA-256, a non-password hash)
  - Tokens are signed JWTs with expiry (were plain "token::<email>" strings)
  - Separate access + refresh tokens with different TTLs
  - Token verification is cryptographic, not a string-prefix check
"""

import os
import random
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from jose import JWTError
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.state import USERS_DB, OTP_DB, new_id
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
# Limiter is injected via request.app.state.limiter; we'll use a local shim that
# delegates so we don't need a circular import with main.py
from slowapi import _rate_limit_exceeded_handler

# Instead of defining a second limiter here that hardcodes `get_remote_address`,
# we import the shared one we define in a new module. Let's assume we create core.limiter.
from core.limiter import limiter


OTP_TTL = 120  # 2 minutes


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _send_sms(mobile: str, otp: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    if not account_sid or not auth_token or not from_number:
        print(f"\n[DAKSHA OTP] Mobile: {mobile}  OTP: {otp}  (Twilio not configured)\n")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={
                "From": from_number,
                "To": f"+91{mobile}",
                "Body": (
                    f"Welcome to Daksha! Your verification OTP is {otp}. "
                    "It expires in 2 minutes. Never share this with anyone."
                ),
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"[DAKSHA SMS ERROR] {resp.text}")
            raise HTTPException(status_code=502, detail="Failed to send OTP via SMS")


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class SendOtpPayload(BaseModel):
    mobile: str


class VerifyOtpPayload(BaseModel):
    mobile: str
    otp: str


# ─────────────────────────────────────────────────────────────────────────────
# OTP routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/send-otp")
@limiter.limit("5/minute")
async def send_otp(request: Request, payload: SendOtpPayload) -> dict:
    mobile = payload.mobile.strip()
    if len(mobile) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number")
    otp = str(random.randint(100000, 999999))
    expires_at = time.time() + OTP_TTL
    OTP_DB[mobile] = {"otp": otp, "expires_at": expires_at}
    await _send_sms(mobile, otp)
    return {"message": "OTP sent"}


@router.post("/verify-otp")
async def verify_otp(request: Request, payload: VerifyOtpPayload) -> dict:
    mobile = payload.mobile.strip()
    record = OTP_DB.get(mobile)
    if not record:
        raise HTTPException(status_code=400, detail="No OTP sent to this number")
    if time.time() > record["expires_at"]:
        del OTP_DB[mobile]
        raise HTTPException(status_code=400, detail="OTP expired")
    if payload.otp.strip() != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    del OTP_DB[mobile]
    return {"verified": True}


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/register")
@limiter.limit("10/minute")
def register(request: Request, req: RegisterRequest) -> dict:
    if req.email in USERS_DB:
        raise HTTPException(status_code=409, detail="User already exists")
    user = {
        "id": new_id("user"),
        "email": req.email,
        "password": hash_password(req.password),  # bcrypt — NOT sha256
        "name": req.name or "",
        "role": "user",
    }
    USERS_DB[req.email] = user
    return {
        "message": "User registered successfully",
        "user": {k: v for k, v in user.items() if k != "password"},
    }


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest) -> dict:
    user = USERS_DB.get(req.email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(subject=req.email)
    refresh_token = create_refresh_token(subject=req.email)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {k: v for k, v in user.items() if k != "password"},
    }


@router.post("/refresh")
def refresh_token_endpoint(req: RefreshRequest) -> dict:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        email = decode_token(req.refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired refresh token: {exc}") from exc

    if email not in USERS_DB:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(subject=email)
    new_refresh = create_refresh_token(subject=email)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }