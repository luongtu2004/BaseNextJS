from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CustomerIndustryCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str | None
    code: str | None
    slug: str | None = None
    description: str | None
    icon_url: str | None = None
    service_categories: list[CustomerServiceCategory] = []


class CustomerServiceCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    industry_category_id: uuid.UUID
    name: str | None
    code: str | None
    slug: str | None = None
    description: str | None
    icon_url: str | None = None


class CustomerSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_category_id: uuid.UUID
    name: str
    code: str | None = None
    description: str | None


class CustomerProviderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_full_name: str | None
    provider_type: str
    description: str | None
    avg_rating: float
    total_reviews: int
    total_jobs_completed: int
    avatar_url: str | None
    address: str | None = None


class CustomerIndividualProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str | None
    exe_year: int | None
    cccd: str | None


class CustomerBusinessProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    company_name: str
    exe_year: int | None
    legal_name: str | None
    tax_code: str | None
    business_license_number: str | None
    representative_name: str | None
    representative_position: str | None
    founded_date: date | None
    hotline: str | None
    website_url: str | None


class CustomerProviderDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    individual_profile: CustomerIndividualProfile | None = None
    business_profile: CustomerBusinessProfile | None = None


class CustomerProviderService(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_category_name: str
    description: str | None
    base_price: float | None
    unit: str | None
    skills: list[str]
