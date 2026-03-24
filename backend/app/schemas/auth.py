from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class OtpSendRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class OtpSendResponse(BaseModel):
    otp_session_id: uuid.UUID
    expired_in: int


class OtpVerifyRequest(BaseModel):
    phone: str
    otp_code: str
    otp_session_id: uuid.UUID
    purpose: str | None = "general"


class OtpVerifyResponse(BaseModel):
    is_valid: bool
    verification_token: str | None = None


class RegisterRequest(BaseModel):
    phone: str
    otp_verification_token: str | None = None
    otp_code: str | None = None
    otp_session_id: uuid.UUID | None = None
    full_name: str | None = None
    password: str | None = None
    gender: int | None = None
    dob: date | None = None


class LoginOtpRequest(BaseModel):
    phone: str
    otp_verification_token: str | None = None
    otp_code: str | None = None
    otp_session_id: uuid.UUID | None = None


class LoginPasswordRequest(BaseModel):
    phone: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class UserItem(BaseModel):
    id: uuid.UUID
    phone: str | None
    full_name: str | None
    gender: int | None
    dob: date | None
    avatar_url: str | None
    phone_verified: bool
    status: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserItem
    roles: list[str]
