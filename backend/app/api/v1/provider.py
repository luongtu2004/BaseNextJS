import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, check_user_role
from app.db.session import get_db
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile
from app.models.provider_service import ProviderService, ProviderServiceAttribute
from app.models.taxonomy import IndustryCategory, ServiceCategory, ServiceSkill
from app.models.user import User
from app.schemas.provider import (
    ProviderMeResponse,
    ProviderProfileUpdateRequest,
    ProviderServiceAttributeValue,
    ProviderServiceCreateRequest,
    ProviderServiceResponse,
)

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
