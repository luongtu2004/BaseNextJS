from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CustomerIndustryCategory(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    icon_url: str | None
    description: str | None


class CustomerServiceCategory(BaseModel):
    id: uuid.UUID
    industry_category_id: uuid.UUID
    name: str
    slug: str
    icon_url: str | None
    description: str | None


class CustomerSkill(BaseModel):
    id: uuid.UUID
    service_category_id: uuid.UUID
    name: str
    description: str | None


class CustomerProviderListItem(BaseModel):
    id: uuid.UUID
    owner_full_name: str | None
    provider_type: str
    description: str | None
    avg_rating: float
    total_reviews: int
    total_jobs_completed: int
    avatar_url: str | None
    address: str | None = None


class CustomerProviderDetail(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    owner_full_name: str | None
    provider_type: str
    description: str | None
    avg_rating: float
    total_reviews: int
    total_jobs_completed: int
    created_at: datetime
    avatar_url: str | None
    # Profiles
    individual_profile: dict[str, Any] | None = None
    business_profile: dict[str, Any] | None = None


class CustomerProviderService(BaseModel):
    id: uuid.UUID
    service_category_name: str
    description: str | None
    base_price: float | None
    unit: str | None
    skills: list[str]
