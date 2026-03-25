from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_role
from app.db.session import get_db
from app.models.taxonomy import (
    IndustryCategory,
    ServiceCategory,
    ServiceCategoryAttribute,
    ServiceCategoryRequirement,
    ServiceSkill,
)
from app.models.user import UserRole


# ==================== Industry Category Responses ====================

class IndustryCategoryResponse(BaseModel):
    id: uuid.UUID
    code: str | None
    name: str | None
    description: str | None
    is_active: bool
    created_at: Any
    updated_at: Any


class IndustryCategoryCreateRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class IndustryCategoryUpdateRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ==================== Service Category Responses ====================

class ServiceCategoryResponse(BaseModel):
    id: uuid.UUID
    industry_category_id: uuid.UUID
    code: str | None
    name: str | None
    description: str | None
    is_active: bool
    created_at: Any
    updated_at: Any


class ServiceCategoryCreateRequest(BaseModel):
    industry_category_id: uuid.UUID
    code: str | None = None
    name: str | None = None
    description: str | None = None


class ServiceCategoryUpdateRequest(BaseModel):
    industry_category_id: uuid.UUID | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ==================== Service Skill Responses ====================

class ServiceSkillResponse(BaseModel):
    id: uuid.UUID
    service_category_id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: Any
    updated_at: Any


class ServiceSkillCreateRequest(BaseModel):
    service_category_id: uuid.UUID
    code: str
    name: str
    description: str | None = None


class ServiceSkillUpdateRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ==================== Service Category Attribute Responses ====================

class ServiceCategoryAttributeResponse(BaseModel):
    id: uuid.UUID
    service_category_id: uuid.UUID
    attr_key: str
    attr_label: str
    data_type: str
    is_required: bool
    is_filterable: bool
    is_searchable: bool
    default_value: str | None
    placeholder: str | None
    help_text: str | None
    options_json: dict | list | None
    validation_json: dict | None
    created_at: Any
    updated_at: Any


class ServiceCategoryAttributeCreateRequest(BaseModel):
    service_category_id: uuid.UUID
    attr_key: str
    attr_label: str
    data_type: str
    is_required: bool = False
    is_filterable: bool = False
    is_searchable: bool = False
    default_value: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    options_json: dict | list | None = None
    validation_json: dict | None = None


class ServiceCategoryAttributeUpdateRequest(BaseModel):
    attr_label: str | None = None
    data_type: str | None = None
    is_required: bool | None = None
    is_filterable: bool | None = None
    is_searchable: bool | None = None
    default_value: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    options_json: dict | list | None = None
    validation_json: dict | None = None


# ==================== Service Category Requirement Responses ====================

class ServiceCategoryRequirementResponse(BaseModel):
    id: uuid.UUID
    service_category_id: uuid.UUID
    requirement_type: str
    requirement_code: str
    requirement_name: str
    description: str | None
    is_required: bool
    applies_to_provider_type: str
    is_active: bool
    created_at: Any
    updated_at: Any


class ServiceCategoryRequirementCreateRequest(BaseModel):
    service_category_id: uuid.UUID
    requirement_type: str
    requirement_code: str
    requirement_name: str
    description: str | None = None
    is_required: bool = True
    applies_to_provider_type: str = "all"


class ServiceCategoryRequirementUpdateRequest(BaseModel):
    requirement_type: str | None = None
    requirement_code: str | None = None
    requirement_name: str | None = None
    description: str | None = None
    is_required: bool | None = None
    applies_to_provider_type: str | None = None
    is_active: bool | None = None


# ==================== Router Definition ====================
router = APIRouter(tags=["admin-taxonomy"])


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


# ==================== Industry Categories ====================

@router.get("/industry-categories")
async def list_industry_categories(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    is_active: bool | None = Query(default=None),
) -> list[IndustryCategoryResponse]:
    if is_active is not None:
        stmt = select(IndustryCategory).where(
            IndustryCategory.is_active == is_active
        ).order_by(IndustryCategory.name)
    else:
        stmt = select(IndustryCategory).where(
            IndustryCategory.is_active == True
        ).order_by(IndustryCategory.name)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        IndustryCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        )
        for cat in rows
    ]


@router.post("/industry-categories", response_model=IndustryCategoryResponse)
async def create_industry_category(
    payload: IndustryCategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> IndustryCategoryResponse:
    category = IndustryCategory(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return IndustryCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/industry-categories/{category_id}", response_model=IndustryCategoryResponse)
async def update_industry_category(
    category_id: uuid.UUID,
    payload: IndustryCategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> IndustryCategoryResponse:
    category = await db.get(IndustryCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Industry category not found")
    
    if payload.code is not None:
        category.code = payload.code
    if payload.name is not None:
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description
    if payload.is_active is not None:
        category.is_active = payload.is_active
    
    await db.commit()
    await db.refresh(category)
    
    return IndustryCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.patch("/industry-categories/{category_id}/status")
async def patch_industry_category_status(
    category_id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    category = await db.get(IndustryCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Industry category not found")
    
    category.is_active = is_active
    await db.commit()
    
    return {"success": True, "is_active": is_active}


@router.delete("/industry-categories/{category_id}")
async def delete_industry_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    category = await db.get(IndustryCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Industry category not found")
    
    try:
        await db.delete(category)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete industry category: {str(e)}")
    
    return {"success": True}


# ==================== Service Categories ====================

@router.get("/service-categories")
async def list_service_categories(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    industry_category_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> list[ServiceCategoryResponse]:
    if industry_category_id:
        if is_active is not None:
            stmt = select(ServiceCategory).where(
                and_(
                    ServiceCategory.industry_category_id == industry_category_id,
                    ServiceCategory.is_active == is_active,
                )
            ).order_by(ServiceCategory.name)
        else:
            stmt = select(ServiceCategory).where(
                ServiceCategory.industry_category_id == industry_category_id
            ).order_by(ServiceCategory.name)
    elif is_active is not None:
        stmt = select(ServiceCategory).where(
            ServiceCategory.is_active == is_active
        ).order_by(ServiceCategory.name)
    else:
        stmt = select(ServiceCategory).where(
            ServiceCategory.is_active == True
        ).order_by(ServiceCategory.name)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        ServiceCategoryResponse(
            id=cat.id,
            industry_category_id=cat.industry_category_id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        )
        for cat in rows
    ]


@router.post("/service-categories", response_model=ServiceCategoryResponse)
async def create_service_category(
    payload: ServiceCategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryResponse:
    category = ServiceCategory(
        industry_category_id=payload.industry_category_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return ServiceCategoryResponse(
        id=category.id,
        industry_category_id=category.industry_category_id,
        code=category.code,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/service-categories/{category_id}", response_model=ServiceCategoryResponse)
async def update_service_category(
    category_id: uuid.UUID,
    payload: ServiceCategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryResponse:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    if payload.industry_category_id is not None:
        category.industry_category_id = payload.industry_category_id
    if payload.code is not None:
        category.code = payload.code
    if payload.name is not None:
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description
    if payload.is_active is not None:
        category.is_active = payload.is_active
    
    await db.commit()
    await db.refresh(category)
    
    return ServiceCategoryResponse(
        id=category.id,
        industry_category_id=category.industry_category_id,
        code=category.code,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.patch("/service-categories/{category_id}/status")
async def patch_service_category_status(
    category_id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    category.is_active = is_active
    await db.commit()
    
    return {"success": True, "is_active": is_active}


@router.delete("/service-categories/{category_id}")
async def delete_service_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    try:
        await db.delete(category)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete service category: {str(e)}")
    
    return {"success": True}


# ==================== Service Skills ====================

@router.get("/service-skills")
async def list_service_skills(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    service_category_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> list[ServiceSkillResponse]:
    if service_category_id:
        if is_active is not None:
            stmt = select(ServiceSkill).where(
                and_(
                    ServiceSkill.service_category_id == service_category_id,
                    ServiceSkill.is_active == is_active,
                )
            ).order_by(ServiceSkill.name)
        else:
            stmt = select(ServiceSkill).where(
                ServiceSkill.service_category_id == service_category_id
            ).order_by(ServiceSkill.name)
    elif is_active is not None:
        stmt = select(ServiceSkill).where(
            ServiceSkill.is_active == is_active
        ).order_by(ServiceSkill.name)
    else:
        stmt = select(ServiceSkill).where(
            ServiceSkill.is_active == True
        ).order_by(ServiceSkill.name)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        ServiceSkillResponse(
            id=skill.id,
            service_category_id=skill.service_category_id,
            code=skill.code,
            name=skill.name,
            description=skill.description,
            is_active=skill.is_active,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
        )
        for skill in rows
    ]


@router.post("/service-skills", response_model=ServiceSkillResponse)
async def create_service_skill(
    payload: ServiceSkillCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceSkillResponse:
    skill = ServiceSkill(
        service_category_id=payload.service_category_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    return ServiceSkillResponse(
        id=skill.id,
        service_category_id=skill.service_category_id,
        code=skill.code,
        name=skill.name,
        description=skill.description,
        is_active=skill.is_active,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


@router.put("/service-skills/{skill_id}", response_model=ServiceSkillResponse)
async def update_service_skill(
    skill_id: uuid.UUID,
    payload: ServiceSkillUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceSkillResponse:
    skill = await db.get(ServiceSkill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Service skill not found")
    
    if payload.code is not None:
        skill.code = payload.code
    if payload.name is not None:
        skill.name = payload.name
    if payload.description is not None:
        skill.description = payload.description
    if payload.is_active is not None:
        skill.is_active = payload.is_active
    
    await db.commit()
    await db.refresh(skill)
    
    return ServiceSkillResponse(
        id=skill.id,
        service_category_id=skill.service_category_id,
        code=skill.code,
        name=skill.name,
        description=skill.description,
        is_active=skill.is_active,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


@router.patch("/service-skills/{skill_id}/status")
async def patch_service_skill_status(
    skill_id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    skill = await db.get(ServiceSkill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Service skill not found")
    
    skill.is_active = is_active
    await db.commit()
    
    return {"success": True, "is_active": is_active}


@router.delete("/service-skills/{skill_id}")
async def delete_service_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    skill = await db.get(ServiceSkill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Service skill not found")
    
    try:
        await db.delete(skill)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete service skill: {str(e)}")
    
    return {"success": True}


# ==================== Service Category Attributes ====================

@router.get("/service-categories/{category_id}/attributes")
async def list_service_category_attributes(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> list[ServiceCategoryAttributeResponse]:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    stmt = select(ServiceCategoryAttribute).where(
        ServiceCategoryAttribute.service_category_id == category_id
    ).order_by(ServiceCategoryAttribute.attr_key)
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        ServiceCategoryAttributeResponse(
            id=attr.id,
            service_category_id=attr.service_category_id,
            attr_key=attr.attr_key,
            attr_label=attr.attr_label,
            data_type=attr.data_type,
            is_required=attr.is_required,
            is_filterable=attr.is_filterable,
            is_searchable=attr.is_searchable,
            default_value=attr.default_value,
            placeholder=attr.placeholder,
            help_text=attr.help_text,
            options_json=attr.options_json,
            validation_json=attr.validation_json,
            created_at=attr.created_at,
            updated_at=attr.updated_at,
        )
        for attr in rows
    ]


@router.post("/service-categories/{category_id}/attributes", response_model=ServiceCategoryAttributeResponse)
async def create_service_category_attribute(
    category_id: uuid.UUID,
    payload: ServiceCategoryAttributeCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryAttributeResponse:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    # Check if attr_key already exists
    existing = await db.execute(
        select(ServiceCategoryAttribute).where(
            and_(
                ServiceCategoryAttribute.service_category_id == category_id,
                ServiceCategoryAttribute.attr_key == payload.attr_key,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Attribute key already exists for this category")
    
    attribute = ServiceCategoryAttribute(
        service_category_id=category_id,
        attr_key=payload.attr_key,
        attr_label=payload.attr_label,
        data_type=payload.data_type,
        is_required=payload.is_required,
        is_filterable=payload.is_filterable,
        is_searchable=payload.is_searchable,
        default_value=payload.default_value,
        placeholder=payload.placeholder,
        help_text=payload.help_text,
        options_json=payload.options_json,
        validation_json=payload.validation_json,
    )
    db.add(attribute)
    await db.commit()
    await db.refresh(attribute)
    
    return ServiceCategoryAttributeResponse(
        id=attribute.id,
        service_category_id=attribute.service_category_id,
        attr_key=attribute.attr_key,
        attr_label=attribute.attr_label,
        data_type=attribute.data_type,
        is_required=attribute.is_required,
        is_filterable=attribute.is_filterable,
        is_searchable=attribute.is_searchable,
        default_value=attribute.default_value,
        placeholder=attribute.placeholder,
        help_text=attribute.help_text,
        options_json=attribute.options_json,
        validation_json=attribute.validation_json,
        created_at=attribute.created_at,
        updated_at=attribute.updated_at,
    )


@router.put("/service-category-attributes/{attribute_id}", response_model=ServiceCategoryAttributeResponse)
async def update_service_category_attribute(
    attribute_id: uuid.UUID,
    payload: ServiceCategoryAttributeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryAttributeResponse:
    attribute = await db.get(ServiceCategoryAttribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    if payload.attr_label is not None:
        attribute.attr_label = payload.attr_label
    if payload.data_type is not None:
        attribute.data_type = payload.data_type
    if payload.is_required is not None:
        attribute.is_required = payload.is_required
    if payload.is_filterable is not None:
        attribute.is_filterable = payload.is_filterable
    if payload.is_searchable is not None:
        attribute.is_searchable = payload.is_searchable
    if payload.default_value is not None:
        attribute.default_value = payload.default_value
    if payload.placeholder is not None:
        attribute.placeholder = payload.placeholder
    if payload.help_text is not None:
        attribute.help_text = payload.help_text
    if payload.options_json is not None:
        attribute.options_json = payload.options_json
    if payload.validation_json is not None:
        attribute.validation_json = payload.validation_json
    
    await db.commit()
    await db.refresh(attribute)
    
    return ServiceCategoryAttributeResponse(
        id=attribute.id,
        service_category_id=attribute.service_category_id,
        attr_key=attribute.attr_key,
        attr_label=attribute.attr_label,
        data_type=attribute.data_type,
        is_required=attribute.is_required,
        is_filterable=attribute.is_filterable,
        is_searchable=attribute.is_searchable,
        default_value=attribute.default_value,
        placeholder=attribute.placeholder,
        help_text=attribute.help_text,
        options_json=attribute.options_json,
        validation_json=attribute.validation_json,
        created_at=attribute.created_at,
        updated_at=attribute.updated_at,
    )


@router.delete("/service-category-attributes/{attribute_id}")
async def delete_service_category_attribute(
    attribute_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    attribute = await db.get(ServiceCategoryAttribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    try:
        await db.delete(attribute)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete attribute: {str(e)}")
    
    return {"success": True}


# ==================== Service Category Requirements ====================

@router.get("/service-categories/{category_id}/requirements")
async def list_service_category_requirements(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    is_active: bool | None = Query(default=None),
) -> list[ServiceCategoryRequirementResponse]:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    if is_active is not None:
        stmt = select(ServiceCategoryRequirement).where(
            and_(
                ServiceCategoryRequirement.service_category_id == category_id,
                ServiceCategoryRequirement.is_active == is_active,
            )
        ).order_by(ServiceCategoryRequirement.requirement_name)
    else:
        stmt = select(ServiceCategoryRequirement).where(
            ServiceCategoryRequirement.service_category_id == category_id
        ).order_by(ServiceCategoryRequirement.requirement_name)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        ServiceCategoryRequirementResponse(
            id=req.id,
            service_category_id=req.service_category_id,
            requirement_type=req.requirement_type,
            requirement_code=req.requirement_code,
            requirement_name=req.requirement_name,
            description=req.description,
            is_required=req.is_required,
            applies_to_provider_type=req.applies_to_provider_type,
            is_active=req.is_active,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )
        for req in rows
    ]


@router.post("/service-categories/{category_id}/requirements", response_model=ServiceCategoryRequirementResponse)
async def create_service_category_requirement(
    category_id: uuid.UUID,
    payload: ServiceCategoryRequirementCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryRequirementResponse:
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Service category not found")
    
    # Check if requirement_code already exists
    existing = await db.execute(
        select(ServiceCategoryRequirement).where(
            and_(
                ServiceCategoryRequirement.service_category_id == category_id,
                ServiceCategoryRequirement.requirement_code == payload.requirement_code,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Requirement code already exists for this category")
    
    requirement = ServiceCategoryRequirement(
        service_category_id=category_id,
        requirement_type=payload.requirement_type,
        requirement_code=payload.requirement_code,
        requirement_name=payload.requirement_name,
        description=payload.description,
        is_required=payload.is_required,
        applies_to_provider_type=payload.applies_to_provider_type,
        is_active=True,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    
    return ServiceCategoryRequirementResponse(
        id=requirement.id,
        service_category_id=requirement.service_category_id,
        requirement_type=requirement.requirement_type,
        requirement_code=requirement.requirement_code,
        requirement_name=requirement.requirement_name,
        description=requirement.description,
        is_required=requirement.is_required,
        applies_to_provider_type=requirement.applies_to_provider_type,
        is_active=requirement.is_active,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.put("/service-category-requirements/{requirement_id}", response_model=ServiceCategoryRequirementResponse)
async def update_service_category_requirement(
    requirement_id: uuid.UUID,
    payload: ServiceCategoryRequirementUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> ServiceCategoryRequirementResponse:
    requirement = await db.get(ServiceCategoryRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if payload.requirement_type is not None:
        requirement.requirement_type = payload.requirement_type
    if payload.requirement_code is not None:
        # Check if new code conflicts
        existing = await db.execute(
            select(ServiceCategoryRequirement).where(
                and_(
                    ServiceCategoryRequirement.service_category_id == requirement.service_category_id,
                    ServiceCategoryRequirement.requirement_code == payload.requirement_code,
                    ServiceCategoryRequirement.id != requirement_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Requirement code already exists for this category")
        requirement.requirement_code = payload.requirement_code
    if payload.requirement_name is not None:
        requirement.requirement_name = payload.requirement_name
    if payload.description is not None:
        requirement.description = payload.description
    if payload.is_required is not None:
        requirement.is_required = payload.is_required
    if payload.applies_to_provider_type is not None:
        requirement.applies_to_provider_type = payload.applies_to_provider_type
    if payload.is_active is not None:
        requirement.is_active = payload.is_active
    
    await db.commit()
    await db.refresh(requirement)
    
    return ServiceCategoryRequirementResponse(
        id=requirement.id,
        service_category_id=requirement.service_category_id,
        requirement_type=requirement.requirement_type,
        requirement_code=requirement.requirement_code,
        requirement_name=requirement.requirement_name,
        description=requirement.description,
        is_required=requirement.is_required,
        applies_to_provider_type=requirement.applies_to_provider_type,
        is_active=requirement.is_active,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.patch("/service-category-requirements/{requirement_id}/status")
async def patch_service_category_requirement_status(
    requirement_id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    requirement = await db.get(ServiceCategoryRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    requirement.is_active = is_active
    await db.commit()
    
    return {"success": True, "is_active": is_active}


@router.delete("/service-category-requirements/{requirement_id}")
async def delete_service_category_requirement(
    requirement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    requirement = await db.get(ServiceCategoryRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    try:
        await db.delete(requirement)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete requirement: {str(e)}")
    
    return {"success": True}