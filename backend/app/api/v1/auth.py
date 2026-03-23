from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_otp_verification_token,
    create_refresh_token,
    decode_otp_verification_token,
    decode_refresh_token,
    generate_otp_code,
    hash_otp_code,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import OtpSession, RefreshToken
from app.models.user import User, UserProfile, UserRole
from app.schemas.auth import (
    AuthResponse,
    LoginOtpRequest,
    LoginPasswordRequest,
    LogoutRequest,
    OtpSendRequest,
    OtpSendResponse,
    OtpVerifyRequest,
    OtpVerifyResponse,
    RefreshRequest,
    RegisterRequest,
    UserItem,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit() or ch == "+")


async def _verify_otp_for_phone(
    db: AsyncSession,
    phone: str,
    otp_code: str,
    otp_session_id: uuid.UUID,
) -> None:
    otp_session = await db.get(OtpSession, otp_session_id)
    now = datetime.now(UTC)
    if (
        not otp_session
        or otp_session.phone != phone
        or otp_session.is_used
        or otp_session.expires_at < now
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp_session.attempt_count = int(otp_session.attempt_count) + 1
    if otp_session.attempt_count > settings.otp_max_attempts:
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP attempts exceeded")

    if otp_session.otp_code_hash != hash_otp_code(otp_code):
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp_session.is_used = True
    otp_session.updated_at = now
    await db.commit()


async def _build_auth_response(db: AsyncSession, user: User) -> AuthResponse:
    roles_query = await db.execute(select(UserRole.role_code).where(UserRole.user_id == user.id))
    roles = [x[0] for x in roles_query.all()]
    jti = uuid.uuid4().hex
    refresh_exp = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=refresh_exp,
        )
    )
    await db.commit()
    access_token = create_access_token(str(user.id), roles)
    refresh_token = create_refresh_token(str(user.id), jti)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserItem(
            id=user.id,
            phone=user.phone,
            full_name=user.full_name,
            gender=user.gender,
            dob=user.dob,
            avatar_url=user.avatar_url,
            phone_verified=user.phone_verified,
            status=user.status,
            created_at=user.created_at,
        ),
        roles=roles,
    )


@router.post("/otp/send", response_model=OtpSendResponse)
async def send_otp(payload: OtpSendRequest, db: AsyncSession = Depends(get_db)) -> OtpSendResponse:
    phone = normalize_phone(payload.phone)
    otp_code = generate_otp_code()
    now = datetime.now(UTC)
    otp_session = OtpSession(
        phone=phone,
        otp_code_hash=hash_otp_code(otp_code),
        expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
        attempt_count=0,
        is_used=False,
    )
    db.add(otp_session)
    await db.commit()
    await db.refresh(otp_session)
    # Phase 1 dev: OTP is logged for manual QA.
    print(f"[OTP-DEV] phone={phone} otp={otp_code} session={otp_session.id}")
    return OtpSendResponse(otp_session_id=otp_session.id, expired_in=settings.otp_ttl_seconds)


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def verify_otp(payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)) -> OtpVerifyResponse:
    phone = normalize_phone(payload.phone)
    otp_session = await db.get(OtpSession, payload.otp_session_id)
    if not otp_session or otp_session.phone != phone:
        return OtpVerifyResponse(is_valid=False, verification_token=None)

    now = datetime.now(UTC)
    if otp_session.expires_at < now or otp_session.is_used:
        return OtpVerifyResponse(is_valid=False, verification_token=None)

    otp_session.attempt_count = int(otp_session.attempt_count) + 1
    if otp_session.attempt_count > settings.otp_max_attempts:
        await db.commit()
        return OtpVerifyResponse(is_valid=False, verification_token=None)

    if otp_session.otp_code_hash != hash_otp_code(payload.otp_code):
        await db.commit()
        return OtpVerifyResponse(is_valid=False, verification_token=None)

    otp_session.is_used = True
    otp_session.updated_at = now
    token = create_otp_verification_token(phone, otp_session.id, payload.purpose or "general")
    await db.commit()
    return OtpVerifyResponse(is_valid=True, verification_token=token)


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    phone = normalize_phone(payload.phone)
    if payload.otp_code and payload.otp_session_id:
        await _verify_otp_for_phone(db, phone, payload.otp_code, payload.otp_session_id)
    elif payload.otp_verification_token:
        try:
            token_data = decode_otp_verification_token(payload.otp_verification_token)
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid otp verification token") from exc
        if token_data.get("sub") != phone or token_data.get("typ") != "otp_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid otp verification token")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide otp_code + otp_session_id or otp_verification_token",
        )

    existing = await db.execute(select(User).where(User.phone == phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    user = User(
        phone=phone,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password) if payload.password else None,
        gender=payload.gender,
        dob=payload.dob,
        phone_verified=True,
        status="active",
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="customer"))
    db.add(UserProfile(user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return await _build_auth_response(db, user)


@router.post("/login/otp", response_model=AuthResponse)
async def login_otp(payload: LoginOtpRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    phone = normalize_phone(payload.phone)
    if payload.otp_code and payload.otp_session_id:
        await _verify_otp_for_phone(db, phone, payload.otp_code, payload.otp_session_id)
    elif payload.otp_verification_token:
        try:
            token_data = decode_otp_verification_token(payload.otp_verification_token)
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid otp verification token") from exc
        if token_data.get("sub") != phone or token_data.get("typ") != "otp_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid otp verification token")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide otp_code + otp_session_id or otp_verification_token",
        )

    user_q = await db.execute(select(User).where(User.phone == phone))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return await _build_auth_response(db, user)


@router.post("/login/password", response_model=AuthResponse)
async def login_password(payload: LoginPasswordRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    phone = normalize_phone(payload.phone)
    user_q = await db.execute(select(User).where(User.phone == phone))
    user = user_q.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return await _build_auth_response(db, user)


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        token_data = decode_refresh_token(payload.refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    if token_data.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    user_id = token_data.get("sub")
    jti = token_data.get("jti")
    if not user_id or not jti:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    now = datetime.now(UTC)
    refresh_q = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == uuid.UUID(user_id),
                RefreshToken.jti == jti,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
    )
    refresh_row = refresh_q.scalar_one_or_none()
    if not refresh_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or expired")

    role_rows = await db.execute(select(UserRole.role_code).where(UserRole.user_id == uuid.UUID(user_id)))
    roles = [x[0] for x in role_rows.all()]
    return {"access_token": create_access_token(user_id, roles)}


@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    try:
        token_data = decode_refresh_token(payload.refresh_token)
    except JWTError:
        return {"success": True}
    jti = token_data.get("jti")
    user_id = token_data.get("sub")
    if not jti or not user_id:
        return {"success": True}

    refresh_q = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == uuid.UUID(user_id),
                RefreshToken.jti == jti,
                RefreshToken.revoked_at.is_(None),
            )
        )
    )
    refresh_row = refresh_q.scalar_one_or_none()
    if refresh_row:
        refresh_row.revoked_at = datetime.now(UTC)
        refresh_row.updated_at = datetime.now(UTC)
        await db.commit()
    return {"success": True}
