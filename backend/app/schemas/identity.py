from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class IdentityVerificationCreate(BaseModel):
    verification_type: str = Field(
        default="cccd", description="Loại giấy tờ, vd: cccd, passport, driver_license"
    )


class IdentityFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_type: str
    file_url: str
    uploaded_at: datetime
    is_active: bool


class IdentityVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    verification_type: str
    status: str
    review_mode: str
    full_name_on_id: str | None = None
    date_of_birth_on_id: date | None = None
    gender_on_id: int | None = None
    id_number: str | None = None
    submitted_at: datetime | None = None
    rejection_reason: str | None = None
    note: str | None = None
    is_latest: bool
    created_at: datetime
    updated_at: datetime


class IdentityVerificationDetailResponse(IdentityVerificationResponse):
    files: list[IdentityFileResponse] = []


class IdentityVerificationStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    identity_verification_status: str
    identity_verified_at: datetime | None = None
    latest_identity_verification_id: uuid.UUID | None = None
