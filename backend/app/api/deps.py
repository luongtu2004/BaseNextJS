from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import safe_decode
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginPasswordRequest

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login/password",
    description="Đăng nhập bằng số điện thoại và mật khẩu"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = safe_decode(token, "access")
    if not payload or payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_with_role(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user and return it. Role check should be done separately."""
    payload = safe_decode(token, "access")
    if not payload or payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_roles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    rows = await db.execute(select(UserRole.role_code).where(UserRole.user_id == user.id))
    return [x[0] for x in rows.all()]


async def get_current_admin_user(
    current_user: User = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Check if user has admin role"""
    admin_role_exists = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == current_user.id,
                UserRole.role_code == "admin",
            )
        )
    )
    if not admin_role_exists.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


async def get_current_user_with_specific_role(
    current_user: User = Depends(get_current_user_with_role),
    role_code: str = Depends(),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Check if user has a specific role"""
    role_exists = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == current_user.id,
                UserRole.role_code == role_code,
            )
        )
    )
    if not role_exists.scalar_one_or_none():
        raise HTTPException(status_code=403, detail=f"{role_code} role required")
    return current_user
