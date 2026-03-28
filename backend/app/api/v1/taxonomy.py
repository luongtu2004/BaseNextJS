from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.taxonomy import IndustryCategory, ServiceCategory, ServiceSkill

router = APIRouter()


@router.get("/industry-categories", response_model=list[dict[str, Any]])
async def get_industry_categories(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách tất cả ngành nghề (Industry Categories)"""
    result = await db.execute(
        IndustryCategory.__table__.select().order_by(IndustryCategory.name)
    )
    categories = result.fetchall()
    return [dict(cat._mapping) for cat in categories]


@router.get("/service-categories/{industry_category_id}", response_model=list[dict[str, Any]])
async def get_service_categories(
    industry_category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách dịch vụ theo ngành nghề"""
    result = await db.execute(
        ServiceCategory.__table__.select().where(
            ServiceCategory.industry_category_id == industry_category_id
        ).order_by(ServiceCategory.name)
    )
    categories = result.fetchall()
    return [dict(cat._mapping) for cat in categories]


@router.get("/skills/{service_category_id}", response_model=list[dict[str, Any]])
async def get_skills(
    service_category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách kỹ năng theo dịch vụ"""
    result = await db.execute(
        ServiceSkill.__table__.select().where(
            ServiceSkill.service_category_id == service_category_id
        ).order_by(ServiceSkill.name)
    )
    skills = result.fetchall()
    return [dict(skill._mapping) for skill in skills]


@router.post("/seed-taxonomy", response_model=dict[str, str])
async def seed_taxonomy_data(db: AsyncSession = Depends(get_db)):
    """Seed dữ liệu taxonomy từ constants.ts vào PostgreSQL"""
    from lib.constants import PILLARS
    
    for pillar in PILLARS:
        # Tạo Industry Category
        industry_cat = IndustryCategory(
            code=pillar['id'],
            name=pillar['title'],
            description=pillar['description'],
            is_active=True
        )
        db.add(industry_cat)
        await db.flush()
        
        # Tạo Service Categories (Industries)
        for industry in pillar['industries']:
            service_cat = ServiceCategory(
                industry_category_id=industry_cat.id,
                code=industry.replace(' ', '_').replace('/', '_')[:50],
                name=industry,
                description=None,
                is_active=True
            )
            db.add(service_cat)
            await db.flush()
            
            # Tạo Service Skill cho mỗi industry
            skill = ServiceSkill(
                service_category_id=service_cat.id,
                code=industry.replace(' ', '_').replace('/', '_').replace('.', '_')[:50],
                name=industry,
                description=None,
                is_active=True
            )
            db.add(skill)
    
    await db.commit()
    return {"message": "Taxonomy data seeded successfully"}