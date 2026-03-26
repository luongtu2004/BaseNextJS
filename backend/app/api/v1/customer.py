import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile
from app.models.taxonomy import IndustryCategory, ServiceCategory, ServiceSkill
from app.models.user import User, UserRole
from app.schemas.customer import (
    CustomerIndustryCategory,
    CustomerProviderDetail,
    CustomerProviderListItem,
    CustomerServiceCategory,
    CustomerSkill,
)

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
                owner_full_name=p.owner.full_name if p.owner else None,
                provider_type=p.provider_type,
                description=p.description,
                avg_rating=float(p.avg_rating),
                total_reviews=p.total_reviews,
                total_jobs_completed=p.total_jobs_completed,
                avatar_url=p.owner.avatar_url if p.owner else None
            )
            for p in providers
        ],
        "page": page,
        "page_size": page_size
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
        owner_full_name=provider.owner.full_name if provider.owner else None,
        provider_type=provider.provider_type,
        description=provider.description,
        avg_rating=float(provider.avg_rating),
        total_reviews=provider.total_reviews,
        total_jobs_completed=provider.total_jobs_completed,
        created_at=provider.created_at,
        avatar_url=provider.owner.avatar_url if provider.owner else None,
        individual_profile=provider.individual_profile.__dict__ if provider.individual_profile else None,
        business_profile=provider.business_profile.__dict__ if provider.business_profile else None
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
    
    # 4. Tạo Profile mặc định theo loại
    if provider_type == "individual":
        db.add(ProviderIndividualProfile(provider_id=new_provider.id, full_name=current_user.full_name))
    else:
        db.add(ProviderBusinessProfile(provider_id=new_provider.id, company_name=f"{current_user.full_name}'s Business"))
        
    await db.commit()
    return {"message": "Success! Your provider profile is created and pending review.", "provider_id": new_provider.id}
