from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.provider import Provider, ProviderDocument, ProviderIndividualProfile, ProviderBusinessProfile, ProviderStatusLog
from app.models.provider_service import ProviderService, ProviderDocumentService
from app.models.taxonomy import ServiceCategoryRequirement
from app.models.user import User, UserRole
from app.schemas.admin import ProviderCreateRequest, ProviderUpdateRequest, DocumentReviewRequest


router = APIRouter(tags=["admin-providers"])


@router.get("")
async def list_providers(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    status: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    provider_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> dict:
    """Danh sách providers với tìm kiếm và lọc"""
    conditions = []
    
    if status:
        conditions.append(Provider.status == status)
    
    if verification_status:
        conditions.append(Provider.verification_status == verification_status)
    
    if provider_type:
        conditions.append(Provider.provider_type == provider_type)
    
    # Get base query
    base_stmt = select(Provider).join(User, Provider.owner_user_id == User.id).outerjoin(
        ProviderBusinessProfile, Provider.id == ProviderBusinessProfile.provider_id
    )
    
    if conditions:
        base_stmt = base_stmt.where(and_(*conditions))
    
    # Count total
    count_stmt = select(1).select_from(Provider).join(User, Provider.owner_user_id == User.id)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Get paginated results
    stmt = (
        base_stmt
        .order_by(Provider.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    
    result = {
        "items": [],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
    
    for provider in rows:
        provider_data = {
            "id": provider.id,
            "provider_type": provider.provider_type,
            "description": provider.description,
            "verification_status": provider.verification_status,
            "status": provider.status,
            "avg_rating": float(provider.avg_rating) if provider.avg_rating else 0,
            "total_reviews": provider.total_reviews,
            "total_jobs_completed": provider.total_jobs_completed,
            "owner": {
                "id": provider.owner.id,
                "phone": provider.owner.phone,
                "full_name": provider.owner.full_name,
                "status": provider.owner.status,
            },
            "created_at": provider.created_at,
            "updated_at": provider.updated_at,
        }
        
        # Add individual or business profile
        if provider.individual_profile:
            provider_data["profile"] = {
                "type": "individual",
                "full_name": provider.individual_profile.full_name,
                "exe_year": provider.individual_profile.exe_year,
                "cccd": provider.individual_profile.cccd,
            }
        elif provider.business_profile:
            provider_data["profile"] = {
                "type": "business",
                "company_name": provider.business_profile.company_name,
                "legal_name": provider.business_profile.legal_name,
                "tax_code": provider.business_profile.tax_code,
                "representative_name": provider.business_profile.representative_name,
            }
        
        result["items"].append(provider_data)
    
    return result


# ==================== Provider Document Review ====================

@router.get("/documents")
async def list_provider_documents(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Danh sách giấy tờ của các provider (A26)"""
    conditions = []
    if status:
        conditions.append(ProviderDocument.verification_status == status)
    
    stmt = (
        select(ProviderDocument)
        .order_by(ProviderDocument.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    rows = (await db.execute(stmt)).scalars().all()
    return rows


# ==================== Provider Qualification Console ====================

@router.get("/provider-services/qualification")
async def list_pending_qualifications(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Các dịch vụ cần check điều kiện (A30)"""
    # Lấy các dịch vụ có trạng thái pending chuyên môn
    stmt = select(ProviderService).where(ProviderService.verification_status == "pending")
    rows = (await db.execute(stmt)).scalars().all()
    return rows


# ==================== Provider Completion Tracking ====================

@router.get("/incomplete")
async def list_incomplete_providers(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Provider chưa hoàn thiện hồ sơ (A33)"""
    # Logic đơn giản: Lấy các provider có verification_status = pending
    stmt = select(Provider).where(Provider.verification_status == "pending")
    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.get("/{provider_id}")
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Chi tiết provider"""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider_data = {
        "id": provider.id,
        "provider_type": provider.provider_type,
        "description": provider.description,
        "verification_status": provider.verification_status,
        "status": provider.status,
        "avg_rating": float(provider.avg_rating) if provider.avg_rating else 0,
        "total_reviews": provider.total_reviews,
        "total_jobs_completed": provider.total_jobs_completed,
        "owner": {
            "id": provider.owner.id,
            "phone": provider.owner.phone,
            "full_name": provider.owner.full_name,
            "gender": provider.owner.gender,
            "dob": provider.owner.dob,
            "avatar_url": provider.owner.avatar_url,
            "status": provider.owner.status,
            "phone_verified": provider.owner.phone_verified,
        },
        "created_at": provider.created_at,
        "updated_at": provider.updated_at,
    }
    
    # Add individual or business profile
    if provider.individual_profile:
        provider_data["profile"] = {
            "type": "individual",
            "full_name": provider.individual_profile.full_name,
            "exe_year": provider.individual_profile.exe_year,
            "cccd": provider.individual_profile.cccd,
            "created_at": provider.individual_profile.created_at,
            "updated_at": provider.individual_profile.updated_at,
        }
    elif provider.business_profile:
        bp = provider.business_profile
        provider_data["profile"] = {
            "type": "business",
            "company_name": bp.company_name,
            "exe_year": bp.exe_year,
            "legal_name": bp.legal_name,
            "tax_code": bp.tax_code,
            "business_license_number": bp.business_license_number,
            "representative_name": bp.representative_name,
            "representative_position": bp.representative_position,
            "founded_date": bp.founded_date,
            "hotline": bp.hotline,
            "website_url": bp.website_url,
            "created_at": bp.created_at,
            "updated_at": bp.updated_at,
        }
    
    # Add documents
    documents = await db.execute(
        select(ProviderDocument).where(ProviderDocument.provider_id == provider_id)
    )
    provider_data["documents"] = [
        {
            "id": doc.id,
            "document_type": doc.document_type,
            "document_name": doc.document_name,
            "document_number": doc.document_number,
            "verification_status": doc.verification_status,
            "created_at": doc.created_at,
        }
        for doc in documents.scalars().all()
    ]
    
    return provider_data


@router.patch("/{provider_id}/status")
async def update_provider_status(
    provider_id: uuid.UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    reason: str | None = None,
) -> dict[str, Any]:
    """Cập nhật trạng thái provider"""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    valid_statuses = ["active", "inactive", "blocked"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    old_status = provider.status
    provider.status = status
    
    # Log status change
    status_log = ProviderStatusLog(
        provider_id=provider_id,
        old_status=old_status,
        new_status=status,
        changed_by=admin_user.id,
        reason=reason,
    )
    db.add(status_log)
    
    await db.commit()
    await db.refresh(provider)
    
    return {
        "success": True,
        "provider_id": provider_id,
        "old_status": old_status,
        "new_status": status,
    }


@router.patch("/{provider_id}/verification-status")
async def update_provider_verification_status(
    provider_id: uuid.UUID,
    verification_status: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    note: str | None = None,
) -> dict[str, Any]:
    """Cập nhật trạng thái verification của provider"""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    valid_statuses = ["pending", "approved", "rejected", "suspended"]
    if verification_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid verification_status. Must be one of: {valid_statuses}")
    
    old_verification_status = provider.verification_status
    
    # If approving, check if owner's identity is verified
    if verification_status == "approved":
        # Load owner if not loaded
        if not provider.owner:
            owner = await db.get(User, provider.owner_user_id)
        else:
            owner = provider.owner
            
        if owner.identity_verification_status != "verified":
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot approve provider. Owner's identity status is '{owner.identity_verification_status}'. It must be 'verified' first."
            )

    provider.verification_status = verification_status
    
    # Log if approved or rejected
    if verification_status in ["approved", "rejected"] and note:
        # Update the most recent status log if exists
        status_logs = await db.execute(
            select(ProviderStatusLog).where(ProviderStatusLog.provider_id == provider_id)
            .order_by(ProviderStatusLog.created_at.desc()).limit(1)
        )
        most_recent_log = status_logs.scalar_one_or_none()
        if most_recent_log:
            most_recent_log.rejection_reason = note if verification_status == "rejected" else None
    
    await db.commit()
    await db.refresh(provider)
    
    return {
        "success": True,
        "provider_id": provider_id,
        "old_verification_status": old_verification_status,
        "new_verification_status": verification_status,
    }


@router.post("/import")
async def import_providers(
    provider_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Import provider từ user có role provider_owner"""
    imported_count = 0
    failed_count = 0
    results = []
    
    for user_id in provider_ids:
        user = await db.get(User, user_id)
        if not user:
            failed_count += 1
            results.append({"user_id": user_id, "success": False, "error": "User not found"})
            continue
        
        # Check if user has provider_owner role
        role_check = await db.execute(
            select(UserRole).where(and_(UserRole.user_id == user_id, UserRole.role_code == "provider_owner"))
        )
        if not role_check.scalar_one_or_none():
            failed_count += 1
            results.append({"user_id": user_id, "success": False, "error": "User does not have provider_owner role"})
            continue
        
        # Check if already has provider
        existing_provider = await db.execute(
            select(Provider).where(Provider.owner_user_id == user_id)
        )
        if existing_provider.scalar_one_or_none():
            failed_count += 1
            results.append({"user_id": user_id, "success": False, "error": "User already has provider"})
            continue
        
        # Create provider
        provider = Provider(
            owner_user_id=user_id,
            provider_type="individual",
            description="Imported provider",
            verification_status="pending",
            status="active",
            avg_rating=0,
            total_reviews=0,
            total_jobs_completed=0,
            created_by=admin_user.id,
        )
        db.add(provider)
        await db.flush()
        
        # Create individual profile
        individual_profile = ProviderIndividualProfile(
            provider_id=provider.id,
            full_name=user.full_name,
            cccd=None,
        )
        db.add(individual_profile)
        
        imported_count += 1
        results.append({"user_id": user_id, "success": True, "provider_id": provider.id})
    
    await db.commit()
    
    return {
        "success": True,
        "imported_count": imported_count,
        "failed_count": failed_count,
        "results": results,
    }


@router.post("/manual-create", response_model=dict)
async def manual_create_provider(
    payload: ProviderCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Tạo provider thủ công"""
    # Check if user exists and has provider_owner role
    user = await db.get(User, payload.owner_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role_check = await db.execute(
        select(UserRole).where(and_(UserRole.user_id == payload.owner_user_id, UserRole.role_code == "provider_owner"))
    )
    if not role_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User does not have provider_owner role")
    
    # Check if already has provider
    existing = await db.execute(
        select(Provider).where(Provider.owner_user_id == payload.owner_user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already has a provider")
    
    # Create provider
    provider = Provider(
        owner_user_id=payload.owner_user_id,
        provider_type=payload.provider_type,
        description=payload.description,
        verification_status=payload.verification_status or "pending",
        status=payload.status or "active",
        avg_rating=0,
        total_reviews=0,
        total_jobs_completed=0,
    )
    db.add(provider)
    await db.flush()
    
    # Create profile based on type
    if payload.provider_type == "individual":
        profile = ProviderIndividualProfile(
            provider_id=provider.id,
            full_name=user.full_name,
            cccd=payload.cccd,
        )
    else:
        profile = ProviderBusinessProfile(
            provider_id=provider.id,
            company_name=payload.company_name or "",
            legal_name=payload.legal_name,
            tax_code=payload.tax_code,
            business_license_number=payload.business_license_number,
            representative_name=payload.representative_name,
            representative_position=payload.representative_position,
        )
    db.add(profile)
    
    await db.commit()
    await db.refresh(provider)
    
    return {
        "success": True,
        "provider": {
            "id": provider.id,
            "owner_user_id": provider.owner_user_id,
            "provider_type": provider.provider_type,
            "verification_status": provider.verification_status,
            "status": provider.status,
        },
    }


# ==================== Provider Document Review ====================



@router.get("/documents/{id}")
async def get_provider_document_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Chi tiết giấy tờ (A27)"""
    doc = await db.get(ProviderDocument, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/documents/{id}/review")
async def review_provider_document(
    id: uuid.UUID,
    payload: DocumentReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Duyệt hoặc từ chối chứng chỉ/giấy tờ (A28, A29)"""
    doc = await db.get(ProviderDocument, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.verification_status = payload.status
    doc.rejection_reason = payload.reason if payload.status == "rejected" else None
    doc.verified_at = func.now() if payload.status == "approved" else None
    doc.verified_by = admin_user.id if payload.status == "approved" else None
    doc.updated_by = admin_user.id
    
    await db.commit()
    return {"message": f"Document status updated to {payload.status}"}


# ==================== Provider Qualification Console ====================



@router.get("/provider-services/{id}/qualification")
async def get_service_qualification_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Chi tiết qualification của một dịch vụ (A31)"""
    svc = await db.get(ProviderService, id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service registration not found")
        
    # Get requirements
    req_stmt = select(ServiceCategoryRequirement).where(
        and_(
            ServiceCategoryRequirement.service_category_id == svc.service_category_id,
            ServiceCategoryRequirement.is_active == True
        )
    )
    reqs = (await db.execute(req_stmt)).scalars().all()
    
    # Get linked documents
    link_stmt = select(ProviderDocument).join(
        ProviderDocumentService, ProviderDocument.id == ProviderDocumentService.provider_document_id
    ).where(ProviderDocumentService.provider_service_id == id)
    docs = (await db.execute(link_stmt)).scalars().all()
    
    return {
        "service": svc,
        "requirements": reqs,
        "linked_documents": docs
    }


@router.post("/provider-services/{id}/qualification/recheck")
async def recheck_qualification(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Ép check lại điều kiện (A32)"""
    # Trong thực tế, đây có thể là trigger một background task hoặc chạy logic khớp document ngay lập tức
    return {"message": "Qualification check re-triggered for service"}


# ==================== Provider Completion Tracking ====================



@router.get("/{id}/completion-summary")
async def get_provider_completion_summary(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Thống kê thiếu gì (A34)"""
    provider = await db.get(Provider, id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    # Reuse provider logic if possible, or implement simple check here
    missing = []
    if not provider.description: missing.append("description")
    
    return {
        "provider_id": id,
        "missing_fields": missing,
        "is_complete": len(missing) == 0
    }


