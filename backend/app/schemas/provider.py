from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class ProviderMeResponse(BaseModel):
    id: uuid.UUID
    provider_type: str
    status: str
    verification_status: str
    avg_rating: float
    total_reviews: int
    total_jobs_completed: int
    created_at: datetime


class ProviderProfileUpdateRequest(BaseModel):
    description: str | None = None
    # Individual fields
    full_name: str | None = None
    exe_year: int | None = None
    cccd: str | None = None
    # Business fields
    company_name: str | None = None
    legal_name: str | None = None
    tax_code: str | None = None
    business_license_number: str | None = None
    representative_name: str | None = None
    representative_position: str | None = None
    founded_date: date | None = None
    hotline: str | None = None
    website_url: str | None = None


class ProviderIndividualProfileUpdate(BaseModel):
    full_name: str | None = None
    exe_year: int | None = None
    cccd: str | None = None


class ProviderBusinessProfileUpdate(BaseModel):
    company_name: str | None = None
    exe_year: int | None = None
    legal_name: str | None = None
    tax_code: str | None = None
    business_license_number: str | None = None
    representative_name: str | None = None
    representative_position: str | None = None
    founded_date: date | None = None
    hotline: str | None = None
    website_url: str | None = None


class ProviderServiceCreateRequest(BaseModel):
    industry_category_id: uuid.UUID
    service_category_id: uuid.UUID
    service_skill_id: uuid.UUID | None = None
    exe_year: int | None = None
    pricing_type: str = "negotiable"
    base_price: float | None = None
    price_unit: str | None = None
    description: str | None = None
    is_primary: bool = False


class ProviderServiceResponse(BaseModel):
    id: uuid.UUID
    industry_category_id: uuid.UUID
    service_category_id: uuid.UUID
    service_skill_id: uuid.UUID | None
    pricing_type: str
    base_price: float | None
    price_unit: str | None
    is_active: bool
    verification_status: str
    created_at: datetime


class ProviderServiceAttributeValue(BaseModel):
    attr_key: str
    value_text: str | None = None
    value_number: float | None = None
    value_boolean: bool | None = None
    value_json: Any | None = None


class ProviderDocumentResponse(BaseModel):
    id: uuid.UUID
    document_type: str
    document_name: str | None = None
    document_number: str | None = None
    issued_by: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    front_file_url: str | None = None
    back_file_url: str | None = None
    extra_file_url: str | None = None
    verification_status: str
    rejection_reason: str | None = None
    created_at: datetime


class ProviderDocumentCreateRequest(BaseModel):
    document_type: str
    document_name: str | None = None
    document_number: str | None = None
    issued_by: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
