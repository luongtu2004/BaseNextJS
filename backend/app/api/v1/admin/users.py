from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_role
from app.db.session import get_db
from app.models.identity import UserIdentityVerification as UserIdentity
from app.models.user import User, UserProfile, UserRole, UserStatusLog
from app.schemas.admin import UserCreateRequest, UserUpdateRequest


router = APIRouter(prefix="/api/v1/admin", tags=["admin-users"])


async def get_current_admin_user(
    current_user = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
):
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


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> dict:
    conditions = []
    
    if keyword:
        conditions.append(User.phone.ilike(f"%{keyword}%"))
        conditions.append(User.full_name.ilike(f"%{keyword}%"))
    
    if status:
        conditions.append(User.status == status)
    
    if role:
        role_condition = await db.execute(
            select(UserRole.user_id).where(UserRole.role_code == role)
        )
        role_user_ids = [row[0] for row in role_condition.all()]
        if role_user_ids:
            conditions.append(User.id.in_(role_user_ids))
        else:
            conditions.append(User.id == None)  # No users with this role
    
    count_stmt = select(1).select_from(User).where(and_(*conditions)) if conditions else select(1).select_from(User)
    # Actually count rows
    if conditions:
        count_select = select(User).where(and_(*conditions))
    else:
        count_select = select(User)
    
    total = (await db.execute(count_select)).scalars().all()
    total = len(total)
    
    if conditions:
        stmt = (
            select(User)
            .where(and_(*conditions))
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    else:
        stmt = select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    result = {
        "items": [],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
    
    for user in rows:
        user_roles = await db.execute(
            select(UserRole.role_code).where(UserRole.user_id == user.id)
        )
        roles = [r[0] for r in user_roles.all()]
        
        profile = await db.get(UserProfile, user.id)
        
        user_data = {
            "id": user.id,
            "phone": user.phone,
            "full_name": user.full_name,
            "gender": user.gender,
            "dob": user.dob,
            "avatar_url": user.avatar_url,
            "status": user.status,
            "phone_verified": user.phone_verified,
            "roles": roles,
            "created_at": user.created_at,
        }
        
        if profile:
            user_data["profile"] = {
                "bio": profile.bio,
                "preferred_language": profile.preferred_language,
                "created_at": profile.created_at,
            }
        
        # Check identity verification
        identity = await db.get(UserIdentity, user.id)
        if identity:
            user_data["identity_verified"] = identity.verification_status == "verified"
        else:
            user_data["identity_verified"] = False
        
        result["items"].append(user_data)
    
    return result


@router.get("/users/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_roles = await db.execute(
        select(UserRole.role_code).where(UserRole.user_id == user.id)
    )
    roles = [r[0] for r in user_roles.all()]
    
    profile = await db.get(UserProfile, user.id)
    
    result = {
        "id": user.id,
        "phone": user.phone,
        "full_name": user.full_name,
        "gender": user.gender,
        "dob": user.dob,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "phone_verified": user.phone_verified,
        "password_hash": user.password_hash,  # Don't expose this in production
        "roles": roles,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
    }
    
    if profile:
        result["profile"] = {
            "bio": profile.bio,
            "preferred_language": profile.preferred_language,
            "timezone": profile.timezone,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
    
    # Check identity verification
    identity = await db.get(UserIdentity, user.id)
    if identity:
        result["identity"] = {
            "verified": identity.verification_status == "verified",
            "id_type": identity.id_type,
            "id_number": identity.id_number,
        }
    
    return result


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, Any]:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate status
    valid_statuses = ["active", "suspended", "banned", "deleted"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    old_status = user.status
    user.status = status
    
    # Log status change
    status_log = UserStatusLog(
        user_id=user_id,
        old_status=old_status,
        new_status=status,
        changed_by=admin_user.id,
    )
    db.add(status_log)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "user_id": user.id,
        "old_status": old_status,
        "new_status": status,
    }


@router.post("/users/create-provider-owner")
async def create_provider_owner(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    # Check if phone already exists
    existing = await db.execute(
        select(User).where(User.phone == payload.phone)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone already registered")
    
    # Create user
    user = User(
        phone=payload.phone,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password) if payload.password else None,
        gender=payload.gender,
        dob=payload.dob,
        avatar_url=payload.avatar_url,
        phone_verified=False,  # Admin must verify
        status="active",
    )
    db.add(user)
    await db.flush()
    
    # Add provider_owner role
    db.add(UserRole(user_id=user.id, role_code="provider_owner"))
    
    # Add default profile
    db.add(UserProfile(user_id=user.id))
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "full_name": user.full_name,
            "roles": ["provider_owner"],
            "created_at": user.created_at,
        },
    }


def hash_password(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)