from __future__ import annotations

import logging
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import safe_decode
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginPasswordRequest

logger = logging.getLogger(__name__)

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
        logger.warning("Invalid access token presented")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Access token missing 'sub' claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        logger.warning("Token valid but user not found - user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    logger.debug("Authenticated user - user_id=%s phone=%s", user.id, user.phone)
    return user


async def get_current_roles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    rows = await db.execute(select(UserRole.role_code).where(UserRole.user_id == user.id))
    return [x[0] for x in rows.all()]


def check_user_role(role_code: str):
    """
    Factory function to create a dependency that checks for a specific role.
    Usage: Depends(check_user_role("admin"))
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(UserRole).where(
            and_(
                UserRole.user_id == current_user.id,
                UserRole.role_code == role_code,
            )
        )
        role_exists = await db.execute(stmt)
        if not role_exists.scalar_one_or_none():
            logger.warning("Role check failed - user_id=%s required_role=%s", current_user.id, role_code)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Role '{role_code}' required"
            )
        return current_user
    
    return role_checker


# Short-cut for common roles
get_current_admin_user = check_user_role("admin")
