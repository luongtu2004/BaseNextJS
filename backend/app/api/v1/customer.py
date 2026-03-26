import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile
from app.models.provider_service import ProviderService
from app.models.taxonomy import IndustryCategory, ServiceCategory, ServiceSkill
from app.models.user import User, UserRole
from app.schemas.customer import (
    CustomerIndustryCategory,
    CustomerProviderDetail,
    CustomerProviderListItem,
    CustomerServiceCategory,
    CustomerSkill,
    CustomerIndividualProfile,
    CustomerBusinessProfile,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/customer", tags=["customer"])


# ==================== Taxonomy ====================

@router.get("/industry-categories", response_model=list[CustomerIndustryCategory])
async def list_industries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách các ngành (Xây dựng, Sửa chữa, v.v.)"""
    stmt = select(IndustryCategory).where(IndustryCategory.is_active == True).order_by(IndustryCategory.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/industry-categories/{industry_id}/service-categories", response_model=list[CustomerServiceCategory])
async def list_services_by_industry(
    industry_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh mục dịch vụ trong một ngành"""
    stmt = select(ServiceCategory).where(
        and_(ServiceCategory.industry_category_id == industry_id, ServiceCategory.is_active == True)
    ).order_by(ServiceCategory.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/service-categories/{category_id}/skills", response_model=list[CustomerSkill])
async def list_skills_by_category(
    category_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách kỹ năng chuyên môn của một dịch vụ"""
    stmt = select(ServiceSkill).where(
        and_(ServiceSkill.service_category_id == category_id, ServiceSkill.is_active == True)
    ).order_by(ServiceSkill.name)
    result = await db.execute(stmt)
    return result.scalars().all()


# ==================== Providers ====================

@router.get("/providers", response_model=dict[str, Any])
async def list_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tìm kiếm thợ trên toàn hệ thống"""
    # Chỉ lấy thợ đang hoạt động và đã được duyệt
    stmt = (
        select(Provider)
        .options(selectinload(Provider.owner))
        .where(and_(Provider.status == "active", Provider.verification_status == "approved"))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    providers = result.scalars().all()
    
    return {
        "items": [
            CustomerProviderListItem(
                id=p.id,
                owner_full_name=str(p.owner.full_name) if p.owner and p.owner.full_name else None,
                provider_type=str(p.provider_type),
                description=str(p.description) if p.description else None,
                avg_rating=float(p.avg_rating),
                total_reviews=int(p.total_reviews),
                total_jobs_completed=int(p.total_jobs_completed),
                avatar_url=str(p.owner.avatar_url) if p.owner and p.owner.avatar_url else None,
                address=str(p.owner.address_line) if p.owner and p.owner.address_line else None
            )
            for p in providers
        ],
        "page": page,
        "page_size": page_size
    }


@router.get("/search", response_model=dict[str, Any])
async def search_providers(
    q: str | None = Query(None, description="Từ khóa hoặc câu lệnh tìm kiếm thợ (vd: thợ khóa tại Hà Nội)"),
    industry_id: uuid.UUID | None = Query(None),
    service_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tìm kiếm thợ thông minh hỗ trợ AI giúp bóc tách ý định người dùng"""
    conditions = [
        Provider.status == "active",
        Provider.verification_status == "approved"
    ]
    
    stmt = (
        select(Provider)
        .join(User, Provider.owner_user_id == User.id)
        .options(selectinload(Provider.owner))
    )
    
    has_service_join = False
    
    if q:
        # 1. Gọi AI bóc tách thông tin (keyword, location)
        ai_data = await AIService.parse_search_prompt(q)
        target_keyword = ai_data.get("keyword") or q
        target_location = ai_data.get("location")
        
        # 2. Xây dựng bộ lọc từ khóa
        q_filter = or_(
            Provider.description.ilike(f"%{target_keyword}%"),
            User.full_name.ilike(f"%{target_keyword}%")
        )
        
        # Nếu AI bóc tách được địa điểm, ưu tiên lọc theo address_line
        if target_location:
            q_filter = or_(q_filter, User.address_line.ilike(f"%{target_location}%"))
        else:
            q_filter = or_(q_filter, User.address_line.ilike(f"%{target_keyword}%"))

        # 3. Join với các bảng Taxonomy để tìm trong tên ngành/dịch vụ
        stmt = stmt.outerjoin(ProviderService, Provider.id == ProviderService.provider_id)
        stmt = stmt.outerjoin(ServiceCategory, ProviderService.service_category_id == ServiceCategory.id)
        stmt = stmt.outerjoin(IndustryCategory, ProviderService.industry_category_id == IndustryCategory.id)
        has_service_join = True
        
        q_filter = or_(
            q_filter,
            ServiceCategory.name.ilike(f"%{target_keyword}%"),
            IndustryCategory.name.ilike(f"%{target_keyword}%"),
            IndustryCategory.code.ilike(f"%{target_keyword}%"),
            ServiceCategory.code.ilike(f"%{target_keyword}%")
        )
        conditions.append(q_filter)
    
    if industry_id:
        if not has_service_join:
            stmt = stmt.join(ProviderService, Provider.id == ProviderService.provider_id)
            has_service_join = True
        conditions.append(ProviderService.industry_category_id == industry_id)
        
    if service_id:
        if not has_service_join:
            stmt = stmt.join(ProviderService, Provider.id == ProviderService.provider_id)
            has_service_join = True
        conditions.append(ProviderService.service_category_id == service_id)

    # Count total
    count_stmt = select(Provider.id).join(User, Provider.owner_user_id == User.id)
    if has_service_join:
        count_stmt = count_stmt.join(ProviderService, Provider.id == ProviderService.provider_id)
        if q:
            count_stmt = count_stmt.outerjoin(ServiceCategory, ProviderService.service_category_id == ServiceCategory.id)
            count_stmt = count_stmt.outerjoin(IndustryCategory, ProviderService.industry_category_id == IndustryCategory.id)
            
    count_stmt = count_stmt.where(and_(*conditions)).distinct()
    total_result = await db.execute(select(func.count()).select_from(count_stmt.subquery()))
    total = total_result.scalar() or 0
    
    # Result collection
    stmt = stmt.where(and_(*conditions)).distinct().offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    providers = result.scalars().all()
    
    return {
        "items": [
            CustomerProviderListItem(
                id=p.id,
                owner_full_name=str(p.owner.full_name) if p.owner and p.owner.full_name else None,
                provider_type=str(p.provider_type),
                description=str(p.description) if p.description else None,
                avg_rating=float(p.avg_rating),
                total_reviews=int(p.total_reviews),
                total_jobs_completed=int(p.total_jobs_completed),
                avatar_url=str(p.owner.avatar_url) if p.owner and p.owner.avatar_url else None,
                address=str(p.owner.address_line) if p.owner and p.owner.address_line else None
            )
            for p in providers
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "ai_debug": {"parsed": ai_data if q else None} # Thêm debug để user kiểm tra
    }


@router.get("/providers/{provider_id}", response_model=CustomerProviderDetail)
async def get_provider_detail(
    provider_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xem hồ sơ chi tiết của một thợ"""
    stmt = (
        select(Provider)
        .options(
            selectinload(Provider.owner),
            selectinload(Provider.individual_profile),
            selectinload(Provider.business_profile)
        )
        .where(Provider.id == provider_id)
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    return CustomerProviderDetail(
        id=provider.id,
        owner_user_id=provider.owner_user_id,
        owner_full_name=str(provider.owner.full_name) if provider.owner and provider.owner.full_name else None,
        provider_type=str(provider.provider_type),
        description=str(provider.description) if provider.description else None,
        avg_rating=float(provider.avg_rating),
        total_reviews=int(provider.total_reviews),
        total_jobs_completed=int(provider.total_jobs_completed),
        created_at=provider.created_at,
        avatar_url=str(provider.owner.avatar_url) if provider.owner and provider.owner.avatar_url else None,
        individual_profile=CustomerIndividualProfile(
            full_name=str(provider.individual_profile.full_name) if provider.individual_profile.full_name else None,
            exe_year=int(provider.individual_profile.exe_year) if provider.individual_profile.exe_year else None,
            cccd=str(provider.individual_profile.cccd) if provider.individual_profile.cccd else None
        ) if provider.individual_profile else None,
        business_profile=CustomerBusinessProfile(
            company_name=str(provider.business_profile.company_name),
            exe_year=int(provider.business_profile.exe_year) if provider.business_profile.exe_year else None,
            legal_name=str(provider.business_profile.legal_name) if provider.business_profile.legal_name else None,
            tax_code=str(provider.business_profile.tax_code) if provider.business_profile.tax_code else None,
            business_license_number=str(provider.business_profile.business_license_number) if provider.business_profile.business_license_number else None,
            representative_name=str(provider.business_profile.representative_name) if provider.business_profile.representative_name else None,
            representative_position=str(provider.business_profile.representative_position) if provider.business_profile.representative_position else None,
            founded_date=provider.business_profile.founded_date,
            hotline=str(provider.business_profile.hotline) if provider.business_profile.hotline else None,
            website_url=str(provider.business_profile.website_url) if provider.business_profile.website_url else None
        ) if provider.business_profile else None
    )


# ==================== Actions ====================

@router.post("/become-provider")
async def become_provider(
    provider_type: str = Query(..., regex="^(individual|business)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Đăng ký trở thành Thợ (Provider) - Yêu cầu đăng nhập"""
    # 1. Kiểm tra xem user đã có hồ sơ provider chưa
    stmt = select(Provider).where(Provider.owner_user_id == current_user.id)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a provider or has a pending request")
    
    # 2. Tạo mới provider
    new_provider = Provider(
        owner_user_id=current_user.id,
        provider_type=provider_type,
        status="active",
        verification_status="pending"  # Phải đợi Admin duyệt
    )
    db.add(new_provider)
    # 3. Thêm Role Provider cho User nếu chưa có
    role_stmt = select(UserRole).where(
        and_(UserRole.user_id == current_user.id, UserRole.role_code == "provider_owner")
    )
    role_exists = await db.execute(role_stmt)
    if not role_exists.scalar_one_or_none():
        db.add(UserRole(user_id=current_user.id, role_code="provider_owner"))
    
    # 4. Tạo Profile mặc định theo loại (Sử dụng relationship để tự động liên kết ID)
    if provider_type == "individual":
        new_provider.individual_profile = ProviderIndividualProfile(full_name=current_user.full_name)
    else:
        new_provider.business_profile = ProviderBusinessProfile(company_name=f"{current_user.full_name}'s Business")
        
    await db.commit()
    return {"message": "Success! Your provider profile is created and pending review.", "provider_id": new_provider.id}
