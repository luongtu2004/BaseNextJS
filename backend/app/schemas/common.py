from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class UserProfileData(BaseModel):
    bio: str | None = None
    preferred_language: str | None = None
    timezone: str | None = None


class MeResponse(BaseModel):
    id: uuid.UUID
    phone: str | None
    full_name: str | None
    gender: int | None
    dob: date | None
    avatar_url: str | None
    roles: list[str]
    profile: UserProfileData | None


class MeUpdateRequest(BaseModel):
    full_name: str | None = None
    gender: int | None = None
    dob: date | None = None
    avatar_url: str | None = None
    bio: str | None = None
    preferred_language: str | None = None


class RoleListResponse(BaseModel):
    roles: list[str]


class PostListItem(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    summary: str | None
    cover_image_url: str | None
    published_at: datetime | None


class PostDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    summary: str | None
    content: str
    cover_image_url: str | None
    published_at: datetime | None
