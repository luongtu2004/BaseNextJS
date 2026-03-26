from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from typing import Optional
from pydantic import BaseModel, Field

from app.api.v1.auth import _build_auth_response, normalize_phone
from app.db.session import get_db
from app.core.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import uuid

swagger_login_router = APIRouter(prefix="/swagger", tags=["swagger-login"])


class SwaggerLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    roles: list[str]


@swagger_login_router.post("/login")
async def swagger_login(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Login endpoint cho Swagger UI OAuth2 form.
    Accepts 'username' and 'password' fields from OAuth2 form.
    Maps 'username' to 'phone'.
    """
    # Swagger UI sends form-encoded data with 'username' and 'password'
    data = await request.form()
    
    phone_val = data.get('username') or data.get('phone')
    password_val = data.get('password')
    
    if not phone_val or not password_val:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing username (phone) or password"
        )
    
    phone = normalize_phone(phone_val)
    
    user_q = await db.execute(select(User).where(User.phone == phone))
    user = user_q.scalar_one_or_none()
    
    if not user or not verify_password(password_val, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    user.last_login_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    await db.commit()
    await db.refresh(user)
    
    auth_response = await _build_auth_response(db, user)
    
    return {
        "access_token": auth_response.access_token,
        "refresh_token": auth_response.refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "full_name": user.full_name,
        },
        "roles": auth_response.roles
    }