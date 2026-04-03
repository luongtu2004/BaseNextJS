from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    phone: str = Field(..., description="Phone number")
    password: str | None = Field(None, description="Password for login")
    full_name: str | None = Field(None, description="Full name")
    gender: int | None = Field(None, description="Gender: 0 for male, 1 for female")
    dob: date | None = Field(None, description="Date of birth")
    avatar_url: str | None = Field(None, description="Avatar URL")


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, description="Full name")
    gender: int | None = Field(None, description="Gender: 0 for male, 1 for female")
    dob: date | None = Field(None, description="Date of birth")
    avatar_url: str | None = Field(None, description="Avatar URL")


class ProviderCreateRequest(BaseModel):
    owner_user_id: uuid.UUID = Field(..., description="Owner user ID")
    provider_type: str = Field(..., description="Type: individual or business")
    description: str | None = Field(None, description="Description")
    verification_status: str | None = Field("pending", description="Verification status")
    status: str | None = Field("active", description="Status")
    # Individual fields
    cccd: str | None = Field(None, description="CCCD for individual")
    # Business fields
    company_name: str | None = Field(None, description="Company name")
    legal_name: str | None = Field(None, description="Legal name")
    tax_code: str | None = Field(None, description="Tax code")
    business_license_number: str | None = Field(None, description="Business license number")
    representative_name: str | None = Field(None, description="Representative name")
    representative_position: str | None = Field(None, description="Representative position")


class ProviderUpdateRequest(BaseModel):
    description: str | None = Field(None, description="Description")
    status: str | None = Field(None, description="Status")
    verification_status: str | None = Field(None, description="Verification status")


class PostCategorySchema(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PostCategoryCreateRequest(BaseModel):
    code: str = Field(..., description="Category code")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="Category slug")
    description: str | None = Field(None, description="Description")


class PostCategoryUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Category name")
    slug: str | None = Field(None, description="Category slug")
    description: str | None = Field(None, description="Description")
    is_active: bool | None = Field(None, description="Is active")


class PostMediaSchema(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    media_type: str
    file_url: str
    thumbnail_url: str | None
    title: str | None
    alt_text: str | None
    is_active: bool
    created_at: datetime


class PostMediaCreateRequest(BaseModel):
    media_type: str = Field(..., description="Type: image, video, document")
    file_url: str = Field(..., description="File URL")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL")
    title: str | None = Field(None, description="Title")
    alt_text: str | None = Field(None, description="Alt text for images")


class PostCreateRequest(BaseModel):
    category_id: uuid.UUID | None = Field(None, description="Category ID")
    author_user_id: uuid.UUID | None = Field(None, description="Author user ID")
    provider_id: uuid.UUID | None = Field(None, description="Provider ID")
    industry_category_id: uuid.UUID | None = Field(None, description="Industry category ID")
    service_category_id: uuid.UUID | None = Field(None, description="Service category ID")
    title: str = Field(..., description="Post title")
    slug: str = Field(..., description="Post slug")
    summary: str | None = Field(None, description="Summary")
    content: str = Field(..., description="Content")
    cover_image_url: str | None = Field(None, description="Cover image URL")
    seo_title: str | None = Field(None, description="SEO title")
    seo_description: str | None = Field(None, description="SEO description")
    post_type: str | None = Field("article", description="Post type: article, promotion, provider_profile, announcement, seo_landing")
    status: str | None = Field("draft", description="Status: draft, pending_review, published, hidden, archived")
    visibility: str | None = Field("public", description="Visibility: public, private, provider_only")
    published_at: datetime | None = Field(None, description="Published at")
    expired_at: datetime | None = Field(None, description="Expired at")
    is_featured: bool | None = Field(False, description="Is featured")
    allow_indexing: bool | None = Field(True, description="Allow indexing")


class PostUpdateRequest(BaseModel):
    category_id: uuid.UUID | None = Field(None, description="Category ID")
    author_user_id: uuid.UUID | None = Field(None, description="Author user ID")
    provider_id: uuid.UUID | None = Field(None, description="Provider ID")
    industry_category_id: uuid.UUID | None = Field(None, description="Industry category ID")
    service_category_id: uuid.UUID | None = Field(None, description="Service category ID")
    title: str | None = Field(None, description="Post title")
    slug: str | None = Field(None, description="Post slug")
    summary: str | None = Field(None, description="Summary")
    content: str | None = Field(None, description="Content")
    cover_image_url: str | None = Field(None, description="Cover image URL")
    seo_title: str | None = Field(None, description="SEO title")
    seo_description: str | None = Field(None, description="SEO description")
    post_type: str | None = Field(None, description="Post type")
    status: str | None = Field(None, description="Status")
    visibility: str | None = Field(None, description="Visibility")
    published_at: datetime | None = Field(None, description="Published at")
    expired_at: datetime | None = Field(None, description="Expired at")
    is_featured: bool | None = Field(None, description="Is featured")
    allow_indexing: bool | None = Field(None, description="Allow indexing")


class PostListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class VerificationReviewRequest(BaseModel):
    reason: str | None = Field(None, description="Reason for rejection or resubmission request")


class DocumentReviewRequest(BaseModel):
    status: str = Field(..., description="approved or rejected")
    reason: str | None = Field(None, description="Reason for rejection")


class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    verification_type: str
    status: str
    full_name_on_id: str | None = None
    id_number: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: uuid.UUID | None = None
    rejection_reason: str | None = None
    created_at: datetime


class VerificationListResponse(BaseModel):
    items: list[VerificationResponse]
    total: int
    page: int
    page_size: int


class UserIdentityFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_type: str
    file_url: str
    uploaded_at: datetime


class VerificationDetailResponse(BaseModel):
    record: VerificationResponse
    files: list[UserIdentityFileSchema]
    user: dict[str, Any]