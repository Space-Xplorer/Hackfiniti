from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import random
import time
import os
import httpx
import hashlib
from dotenv import load_dotenv

load_dotenv()

from api.state import USERS_DB, OTP_DB, create_token, new_id

router = APIRouter(tags=["auth"])

OTP_TTL = 120  # 2 minutes


async def _send_sms(mobile: str, otp: str):
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
                "Body": f"Welcome to Daksha! Your verification OTP is {otp}. It expires in 2 minutes. Never share this with anyone.",
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"[DAKSHA SMS ERROR] {resp.text}")
            raise HTTPException(status_code=502, detail="Failed to send OTP via SMS")


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class SendOtpPayload(BaseModel):
    mobile: str


class VerifyOtpPayload(BaseModel):
    mobile: str
    otp: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/send-otp")
async def send_otp(payload: SendOtpPayload) -> dict:
    mobile = payload.mobile.strip()
    if len(mobile) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number")
    otp = str(random.randint(100000, 999999))
    expires_at = time.time() + OTP_TTL
    OTP_DB[mobile] = {"otp": otp, "expires_at": expires_at}
    await _send_sms(mobile, otp)
    return {"message": "OTP sent"}


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpPayload) -> dict:
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