from __future__ import annotations

import hashlib
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def verify_password(raw_password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return pwd_context.verify(raw_password, password_hash)


def generate_otp_code() -> str:
    min_value = 10 ** (settings.otp_length - 1)
    max_value = (10**settings.otp_length) - 1
    return str(random.randint(min_value, max_value))


def hash_otp_code(code: str) -> str:
    # Deterministic hash with app secret pepper.
    peppered = f"{code}:{settings.jwt_access_secret}"
    return hashlib.sha256(peppered.encode("utf-8")).hexdigest()


def create_otp_verification_token(phone: str, otp_session_id: uuid.UUID, purpose: str = "general") -> str:
    payload: dict[str, Any] = {
        "sub": phone,
        "sid": str(otp_session_id),
        "typ": "otp_verification",
        "purpose": purpose,
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.jwt_access_secret, algorithm="HS256")


def decode_otp_verification_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_access_secret, algorithms=["HS256"])


def create_access_token(user_id: str, roles: list[str]) -> str:
    payload: dict[str, Any] = {
        "sub": user_id,
        "roles": roles,
        "typ": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_access_secret, algorithm="HS256")


def create_refresh_token(user_id: str, jti: str) -> str:
    payload: dict[str, Any] = {
        "sub": user_id,
        "jti": jti,
        "typ": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days),
    }
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_access_secret, algorithms=["HS256"])


def decode_refresh_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_refresh_secret, algorithms=["HS256"])


def safe_decode(token: str, token_type: str) -> dict[str, Any] | None:
    try:
        if token_type == "access":
            return decode_access_token(token)
        if token_type == "refresh":
            return decode_refresh_token(token)
        return decode_otp_verification_token(token)
    except JWTError:
        return None
