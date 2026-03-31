import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.identity import UserIdentityFile, UserIdentityVerification
from app.models.user import User
from app.schemas.admin import VerificationResponse, VerificationReviewRequest

router = APIRouter(tags=["admin-verifications"])


@router.get("/user-verifications", response_model=dict[str, Any])
async def list_user_verifications(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Danh sách hồ sơ xác minh danh tính (A21)"""
    conditions = []
    if status:
        conditions.append(UserIdentityVerification.status == status)

    count_stmt = select(func.count()).select_from(UserIdentityVerification)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(UserIdentityVerification)
        .order_by(UserIdentityVerification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))

    rows = (await db.execute(stmt)).scalars().all()
    
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/user-verifications/{id}")
async def get_user_verification_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Chi tiết hồ sơ xác minh (A22)"""
    stmt = select(UserIdentityVerification).where(UserIdentityVerification.id == id)
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")

    files_stmt = select(UserIdentityFile).where(UserIdentityFile.verification_id == id)
    files = (await db.execute(files_stmt)).scalars().all()

    return {
        "record": record,
        "files": files,
        "user": {
            "id": record.user_id,
            "full_name": record.user.full_name if record.user else None,
            "phone": record.user.phone if record.user else None
        }
    }


@router.post("/user-verifications/{id}/approve")
async def approve_user_verification(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Duyệt xác minh danh tính (A23)"""
    record = await db.get(UserIdentityVerification, id)
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    
    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Chỉ có thể duyệt hồ sơ đã nộp.")

    record.status = "approved"
    record.reviewed_at = func.now()
    record.reviewed_by = admin_user.id
    
    # Update user status
    user = await db.get(User, record.user_id)
    if user:
        user.identity_verification_status = "verified"
        user.identity_verified_at = func.now()

    await db.commit()
    return {"message": "Duyệt hồ sơ thành công"}


@router.post("/user-verifications/{id}/reject")
async def reject_user_verification(
    id: uuid.UUID,
    payload: VerificationReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Từ chối xác minh danh tính (A24)"""
    record = await db.get(UserIdentityVerification, id)
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    
    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Chỉ có thể từ chối hồ sơ đã nộp.")

    record.status = "rejected"
    record.rejection_reason = payload.reason
    record.reviewed_at = func.now()
    record.reviewed_by = admin_user.id
    
    # Update user status
    user = await db.get(User, record.user_id)
    if user:
        user.identity_verification_status = "rejected"

    await db.commit()
    return {"message": "Đã từ chối hồ sơ"}


@router.post("/user-verifications/{id}/request-resubmission")
async def request_resubmission(
    id: uuid.UUID,
    payload: VerificationReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Yêu cầu bổ sung hồ sơ (A25)"""
    record = await db.get(UserIdentityVerification, id)
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    
    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Chỉ có thể yêu cầu bổ sung cho hồ sơ đã nộp.")

    record.status = "draft" # Return to draft for user to edit
    record.rejection_reason = payload.reason # Store reason why it needs resubmission
    
    # Update user status
    user = await db.get(User, record.user_id)
    if user:
        user.identity_verification_status = "unverified"

    await db.commit()
    return {"message": "Đã yêu cầu bổ sung hồ sơ"}
