import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, check_user_role
from app.db.session import get_db
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile, ProviderDocument
from app.models.taxonomy import IndustryCategory, ServiceCategory, ServiceSkill, ServiceCategoryRequirement
from app.models.provider_service import ProviderService, ProviderServiceAttribute, ProviderDocumentService
from app.models.user import User
from app.schemas.provider import (
    ProviderMeResponse,
    ProviderProfileUpdateRequest,
    ProviderServiceAttributeValue,
    ProviderServiceCreateRequest,
    ProviderServiceResponse,
    ProviderIndividualProfileUpdate,
    ProviderBusinessProfileUpdate,
    ProviderDocumentResponse,
    ProviderDocumentCreateRequest,
)
from fastapi import UploadFile, File, Form

router = APIRouter(prefix="/provider", tags=["provider-owner"])


async def get_current_provider(
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db)
) -> Provider:
    """Kiểm tra xem user có Role provider_owner và có hồ sơ Provider không"""
    stmt = select(Provider).where(Provider.owner_user_id == current_user.id)
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=403, detail="User is not a service provider")
    return provider


# ==================== My Profile ====================

@router.get("/me", response_model=ProviderMeResponse)
async def get_my_provider_info(provider: Provider = Depends(get_current_provider)):
    """Lấy thông tin tổng quan của Thợ"""
    return provider


@router.get("/me/profile")
async def get_my_full_profile(
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Lấy hồ sơ chi tiết (Cá nhân/Doanh nghiệp)"""
    if provider.provider_type == "individual":
        profile = await db.get(ProviderIndividualProfile, provider.id)
        return {"provider_type": "individual", "profile": profile}
    else:
        profile = await db.get(ProviderBusinessProfile, provider.id)
        return {"provider_type": "business", "profile": profile}


@router.put("/me/profile")
async def update_my_profile(
    payload: ProviderProfileUpdateRequest,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật thông tin hồ sơ thợ"""
    if payload.description is not None:
        provider.description = payload.description
        
    if provider.provider_type == "individual":
        profile = await db.get(ProviderIndividualProfile, provider.id)
        if profile and payload.full_name:
            profile.full_name = payload.full_name
        if profile and payload.exe_year:
            profile.exe_year = payload.exe_year
        if profile and payload.cccd:
            profile.cccd = payload.cccd
    else:
        profile = await db.get(ProviderBusinessProfile, provider.id)
        if profile:
            if payload.company_name: profile.company_name = payload.company_name
            if payload.tax_code: profile.tax_code = payload.tax_code
            if payload.website_url: profile.website_url = payload.website_url
            # Có thể thêm các trường khác nếu cần
            
    await db.commit()
    return {"message": "Profile updated successfully"}


@router.put("/me/profile/individual")
async def update_individual_profile(
    payload: ProviderIndividualProfileUpdate,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật hồ sơ cá nhân (P4)"""
    if provider.provider_type != "individual":
        raise HTTPException(status_code=400, detail="Provider type is not individual")
    
    profile = await db.get(ProviderIndividualProfile, provider.id)
    if not profile:
        profile = ProviderIndividualProfile(provider_id=provider.id)
        db.add(profile)
        
    if payload.full_name is not None: profile.full_name = payload.full_name
    if payload.exe_year is not None: profile.exe_year = payload.exe_year
    if payload.cccd is not None: profile.cccd = payload.cccd
    
    await db.commit()
    return {"message": "Individual profile updated"}


@router.put("/me/profile/business")
async def update_business_profile(
    payload: ProviderBusinessProfileUpdate,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật hồ sơ doanh nghiệp (P5)"""
    if provider.provider_type != "business":
        raise HTTPException(status_code=400, detail="Provider type is not business")
        
    profile = await db.get(ProviderBusinessProfile, provider.id)
    if not profile:
        profile = ProviderBusinessProfile(provider_id=provider.id, company_name="")
        db.add(profile)
        
    if payload.company_name is not None: profile.company_name = payload.company_name
    if payload.exe_year is not None: profile.exe_year = payload.exe_year
    if payload.legal_name is not None: profile.legal_name = payload.legal_name
    if payload.tax_code is not None: profile.tax_code = payload.tax_code
    if payload.business_license_number is not None: profile.business_license_number = payload.business_license_number
    if payload.representative_name is not None: profile.representative_name = payload.representative_name
    if payload.representative_position is not None: profile.representative_position = payload.representative_position
    if payload.founded_date is not None: profile.founded_date = payload.founded_date
    if payload.hotline is not None: profile.hotline = payload.hotline
    if payload.website_url is not None: profile.website_url = payload.website_url
    
    await db.commit()
    return {"message": "Business profile updated"}


@router.get("/me/profile/completion")
async def get_profile_completion(
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Xem % hoàn thiện hồ sơ & các trường còn thiếu (P6)"""
    fields_to_check = ["description"]
    if provider.provider_type == "individual":
        fields_to_check.extend(["full_name", "cccd", "exe_year"])
        profile = await db.get(ProviderIndividualProfile, provider.id)
    else:
        fields_to_check.extend(["company_name", "tax_code", "business_license_number", "representative_name", "hotline"])
        profile = await db.get(ProviderBusinessProfile, provider.id)
        
    filled_fields = 0
    if provider.description:
        filled_fields += 1
    else:
        missing_fields.append("description")

    if profile:
        for f in fields_to_check:
            if f == "description": continue
            if getattr(profile, f, None):
                filled_fields += 1
            else:
                missing_fields.append(f)
    else:
        missing_fields.extend([f for f in fields_to_check if f != "description"])
            
    completion_rate = int((filled_fields / len(fields_to_check)) * 100)
    
    return {
        "completion_rate": min(completion_rate, 100),
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0
    }


# ==================== Provider Documents ====================

@router.get("/me/documents", response_model=list[ProviderDocumentResponse])
async def list_my_documents(
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Danh sách giấy tờ (P7)"""
    stmt = select(ProviderDocument).where(ProviderDocument.provider_id == provider.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/me/documents", response_model=ProviderDocumentResponse)
async def create_document(
    payload: ProviderDocumentCreateRequest,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Tạo document mới (P8)"""
    new_doc = ProviderDocument(
        provider_id=provider.id,
        document_type=payload.document_type,
        document_name=payload.document_name,
        document_number=payload.document_number,
        issued_by=payload.issued_by,
        issued_date=payload.issued_date,
        expiry_date=payload.expiry_date,
        verification_status="pending"
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc


@router.post("/me/documents/{document_id}/files")
async def upload_document_file(
    document_id: uuid.UUID,
    file_type: str = Form(..., description="front, back, extra"),
    file: UploadFile = File(...),
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Upload file cho document (P9)"""
    doc = await db.get(ProviderDocument, document_id)
    if not doc or doc.provider_id != provider.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.verification_status not in ["pending", "rejected"]:
        raise HTTPException(status_code=400, detail="Cannot upload to a processed document")
        
    # In a real app, use a proper storage service (S3, Cloudinary)
    file_url = f"/uploads/provider_docs/{uuid.uuid4()}_{file.filename}"
    
    if file_type == "front":
        doc.front_file_url = file_url
    elif file_type == "back":
        doc.back_file_url = file_url
    elif file_type == "extra":
        doc.extra_file_url = file_url
    else:
        raise HTTPException(status_code=400, detail="Invalid file_type")
        
    await db.commit()
    return {"message": "File uploaded successfully", "file_url": file_url}


@router.get("/me/documents/{document_id}", response_model=ProviderDocumentResponse)
async def get_document_detail(
    document_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Chi tiết giấy tờ (P10)"""
    doc = await db.get(ProviderDocument, document_id)
    if not doc or doc.provider_id != provider.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/me/documents/{document_id}", response_model=ProviderDocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    payload: ProviderDocumentCreateRequest,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật giấy tờ khi bị từ chối hoặc đang đợi (P11)"""
    doc = await db.get(ProviderDocument, document_id)
    if not doc or doc.provider_id != provider.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.verification_status not in ["pending", "rejected"]:
        raise HTTPException(status_code=400, detail="Cannot update a verified document")
        
    doc.document_type = payload.document_type
    doc.document_name = payload.document_name
    doc.document_number = payload.document_number
    doc.issued_by = payload.issued_by
    doc.issued_date = payload.issued_date
    doc.expiry_date = payload.expiry_date
    doc.verification_status = "pending" # Reset status if updated
    
    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/me/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Xóa tài liệu (P12)"""
    doc = await db.get(ProviderDocument, document_id)
    if not doc or doc.provider_id != provider.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.get("/me/documents/summary")
async def get_documents_summary(
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Thống kê trạng thái giấy tờ (P13)"""
    stmt = select(ProviderDocument).where(ProviderDocument.provider_id == provider.id)
    docs = (await db.execute(stmt)).scalars().all()
    
    summary = {
        "total": len(docs),
        "approved": len([d for d in docs if d.verification_status == "approved"]),
        "pending": len([d for d in docs if d.verification_status == "pending"]),
        "rejected": len([d for d in docs if d.verification_status == "rejected"]),
    }
    return summary


# ==================== Service Qualification ====================

@router.get("/services/{service_id}/requirements")
async def get_service_requirements(
    service_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Xem requirement của service (P15)"""
    stmt = select(ProviderService).where(
        and_(ProviderService.id == service_id, ProviderService.provider_id == provider.id)
    )
    svc = (await db.execute(stmt)).scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    req_stmt = select(ServiceCategoryRequirement).where(
        and_(
            ServiceCategoryRequirement.service_category_id == svc.service_category_id,
            ServiceCategoryRequirement.is_active == True
        )
    ).order_by(ServiceCategoryRequirement.requirement_type)
    reqs = (await db.execute(req_stmt)).scalars().all()
    return reqs


@router.get("/services/{service_id}/qualification")
async def get_service_qualification(
    service_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Check đủ điều kiện chưa (P16)"""
    stmt = select(ProviderService).where(
        and_(ProviderService.id == service_id, ProviderService.provider_id == provider.id)
    )
    svc = (await db.execute(stmt)).scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    # 1. Get requirements
    req_stmt = select(ServiceCategoryRequirement).where(
        and_(
            ServiceCategoryRequirement.service_category_id == svc.service_category_id,
            ServiceCategoryRequirement.is_active == True,
            ServiceCategoryRequirement.is_required == True
        )
    )
    required_reqs = (await db.execute(req_stmt)).scalars().all()
    
    # 2. Get linked approved documents
    link_stmt = select(ProviderDocument).join(
        ProviderDocumentService, ProviderDocument.id == ProviderDocumentService.provider_document_id
    ).where(
        and_(
            ProviderDocumentService.provider_service_id == service_id,
            ProviderDocument.verification_status == "approved"
        )
    )
    approved_docs = (await db.execute(link_stmt)).scalars().all()
    
    # Simplified logic: if there are ANY requirements, check if we have corresponding documents
    # In a real system, we'd match requirement_type/code with document_type
    is_qualified = True
    missing_requirements = []
    
    for req in required_reqs:
        # Check if any approved doc matches this requirement type
        has_doc = any(d.document_type == req.requirement_type for d in approved_docs)
        if not has_doc:
            is_qualified = False
            missing_requirements.append({
                "requirement_code": req.requirement_code,
                "requirement_name": req.requirement_name
            })
            
    return {
        "is_qualified": is_qualified,
        "missing_requirements": missing_requirements,
        "total_required": len(required_reqs),
        "total_approved": len(approved_docs)
    }


@router.put("/services/{service_id}/documents")
async def link_service_documents(
    service_id: uuid.UUID,
    document_ids: list[uuid.UUID],
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Gắn document vào service (P17)"""
    # 1. Verify service ownership
    svc_stmt = select(ProviderService).where(
        and_(ProviderService.id == service_id, ProviderService.provider_id == provider.id)
    )
    svc = (await db.execute(svc_stmt)).scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # 2. Verify documents ownership
    doc_stmt = select(ProviderDocument).where(
        and_(ProviderDocument.id.in_(document_ids), ProviderDocument.provider_id == provider.id)
    )
    docs = (await db.execute(doc_stmt)).scalars().all()
    if len(docs) != len(set(document_ids)):
        raise HTTPException(status_code=400, detail="One or more documents not found or unauthorized")
        
    # 3. Overwrite links
    del_stmt = select(ProviderDocumentService).where(ProviderDocumentService.provider_service_id == service_id)
    old_links = (await db.execute(del_stmt)).scalars().all()
    for link in old_links:
        await db.delete(link)
        
    for doc_id in document_ids:
        new_link = ProviderDocumentService(
            provider_document_id=doc_id,
            provider_service_id=service_id
        )
        db.add(new_link)
        
    await db.commit()
    return {"message": "Service documents updated successfully"}


@router.get("/services/{service_id}/documents", response_model=list[ProviderDocumentResponse])
async def get_service_documents(
    service_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Lấy tài liệu đã gắn (P18)"""
    stmt = select(ProviderDocument).join(
        ProviderDocumentService, ProviderDocument.id == ProviderDocumentService.provider_document_id
    ).where(
        and_(
            ProviderDocumentService.provider_service_id == service_id,
            ProviderDocument.provider_id == provider.id
        )
    )
    docs = (await db.execute(stmt)).scalars().all()
    return docs


# ==================== My Services ====================

@router.get("/services", response_model=list[ProviderServiceResponse])
async def list_my_services(
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Danh sách các dịch vụ mà thợ đã đăng ký cung cấp"""
    stmt = select(ProviderService).where(ProviderService.provider_id == provider.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/services", response_model=ProviderServiceResponse)
async def register_service(
    payload: ProviderServiceCreateRequest,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Đăng ký thêm một dịch vụ mới mà thợ có thể làm"""
    # Kiểm tra xem đã đăng ký dịch vụ này chưa
    check_stmt = select(ProviderService).where(
        and_(
            ProviderService.provider_id == provider.id,
            ProviderService.service_category_id == payload.service_category_id
        )
    )
    existing = await db.execute(check_stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already registered this service")
        
    new_svc = ProviderService(
        provider_id=provider.id,
        industry_category_id=payload.industry_category_id,
        service_category_id=payload.service_category_id,
        service_skill_id=payload.service_skill_id,
        exe_year=payload.exe_year,
        pricing_type=payload.pricing_type,
        base_price=payload.base_price,
        price_unit=payload.price_unit,
        description=payload.description,
        is_primary=payload.is_primary,
        verification_status="pending" # Đợi Admin duyệt chuyên môn
    )
    db.add(new_svc)
    await db.commit()
    await db.refresh(new_svc)
    return new_svc


@router.delete("/services/{service_id}")
async def deactivate_service(
    service_id: uuid.UUID,
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Tạm ngừng cung cấp một dịch vụ"""
    stmt = select(ProviderService).where(
        and_(ProviderService.id == service_id, ProviderService.provider_id == provider.id)
    )
    result = await db.execute(stmt)
    svc = result.scalar_one_or_none()
    
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    svc.is_active = False
    await db.commit()
    return {"message": "Service deactivated"}


@router.patch("/services/{service_id}/attributes")
async def update_service_attributes(
    service_id: uuid.UUID,
    attributes: list[ProviderServiceAttributeValue],
    provider: Provider = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật các thuộc tính động của dịch vụ (ví dụ: máy móc hiện có, v.v.)"""
    # 1. Kiểm tra quyền sở hữu dịch vụ
    svc_stmt = select(ProviderService).where(
        and_(ProviderService.id == service_id, ProviderService.provider_id == provider.id)
    )
    svc = (await db.execute(svc_stmt)).scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # 2. Xóa các thuộc tính cũ và thêm mới (Overwrite)
    del_stmt = select(ProviderServiceAttribute).where(ProviderServiceAttribute.provider_service_id == service_id)
    old_attrs = (await db.execute(del_stmt)).scalars().all()
    for attr in old_attrs:
        await db.delete(attr)
        
    for attr_data in attributes:
        new_attr = ProviderServiceAttribute(
            provider_service_id=service_id,
            attr_key=attr_data.attr_key,
            value_text=attr_data.value_text,
            value_number=attr_data.value_number,
            value_boolean=attr_data.value_boolean,
            value_json=attr_data.value_json
        )
        db.add(new_attr)
        
    await db.commit()
    return {"message": "Service attributes updated"}
