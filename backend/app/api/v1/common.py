from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_roles, get_current_user
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User, UserProfile, UserRole
from app.schemas.common import (
    MeResponse,
    MeUpdateRequest,
    PostDetailResponse,
    PostListItem,
    RoleListResponse,
    UserProfileData,
)

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_roles),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    profile = await db.get(UserProfile, current_user.id)
    return MeResponse(
        id=current_user.id,
        phone=current_user.phone,
        full_name=current_user.full_name,
        gender=current_user.gender,
        dob=current_user.dob,
        avatar_url=current_user.avatar_url,
        roles=roles,
        profile=(
            UserProfileData(
                bio=profile.bio,
                preferred_language=profile.preferred_language,
                timezone=profile.timezone,
            )
            if profile
            else None
        ),
    )


@router.put("/me", response_model=MeResponse)
async def update_me(
    payload: MeUpdateRequest,
    current_user: User = Depends(get_current_user),
    roles: list[str] = Depends(get_current_roles),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    current_user.full_name = payload.full_name if payload.full_name is not None else current_user.full_name
    current_user.gender = payload.gender if payload.gender is not None else current_user.gender
    current_user.dob = payload.dob if payload.dob is not None else current_user.dob
    current_user.avatar_url = payload.avatar_url if payload.avatar_url is not None else current_user.avatar_url

    profile = await db.get(UserProfile, current_user.id)
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.preferred_language is not None:
        profile.preferred_language = payload.preferred_language

    await db.commit()
    await db.refresh(current_user)
    await db.refresh(profile)

    return MeResponse(
        id=current_user.id,
        phone=current_user.phone,
        full_name=current_user.full_name,
        gender=current_user.gender,
        dob=current_user.dob,
        avatar_url=current_user.avatar_url,
        roles=roles,
        profile=UserProfileData(
            bio=profile.bio,
            preferred_language=profile.preferred_language,
            timezone=profile.timezone,
        ),
    )


@router.get("/me/roles", response_model=RoleListResponse)
async def me_roles(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> RoleListResponse:
    rows = await db.execute(select(UserRole.role_code).where(UserRole.user_id == current_user.id))
    return RoleListResponse(roles=[r[0] for r in rows.all()])


@router.get("/posts")
async def list_posts(
    category: uuid.UUID | None = Query(default=None),
    industry_category_id: uuid.UUID | None = Query(default=None),
    service_category_id: uuid.UUID | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    conditions = [Post.status == "published", Post.visibility == "public"]
    if category:
        conditions.append(Post.category_id == category)
    if industry_category_id:
        conditions.append(Post.industry_category_id == industry_category_id)
    if service_category_id:
        conditions.append(Post.service_category_id == service_category_id)
    if keyword:
        conditions.append(or_(Post.title.ilike(f"%{keyword}%"), Post.summary.ilike(f"%{keyword}%")))

    count_stmt = select(func.count()).select_from(Post).where(and_(*conditions))
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(Post)
        .where(and_(*conditions))
        .order_by(Post.published_at.desc().nullslast(), Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            PostListItem(
                id=p.id,
                title=p.title,
                slug=p.slug,
                summary=p.summary,
                cover_image_url=p.cover_image_url,
                published_at=p.published_at,
            ).model_dump()
            for p in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/posts/{slug}", response_model=PostDetailResponse)
async def post_detail(slug: str, db: AsyncSession = Depends(get_db)) -> PostDetailResponse:
    stmt = select(Post).where(
        and_(Post.slug == slug, Post.status == "published", Post.visibility == "public")
    )
    post = (await db.execute(stmt)).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostDetailResponse(
        id=post.id,
        title=post.title,
        slug=post.slug,
        summary=post.summary,
        content=post.content,
        cover_image_url=post.cover_image_url,
        published_at=post.published_at,
    )
