from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.post import Post, PostCategory, PostMedia
from app.models.user import User, UserRole
from app.schemas.admin import (
    PostCategoryCreateRequest,
    PostCategoryUpdateRequest,
    PostCreateRequest,
    PostUpdateRequest,
)


router = APIRouter(tags=["admin-posts"])


# ==================== Post Categories ====================

@router.get("/categories")
async def list_post_categories(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    is_active: bool | None = Query(default=None),
) -> list[dict]:
    """Danh sách danh mục bài viết"""
    if is_active is not None:
        stmt = select(PostCategory).where(
            PostCategory.is_active == is_active
        ).order_by(PostCategory.name)
    else:
        stmt = select(PostCategory).where(
            PostCategory.is_active.is_(True)
        ).order_by(PostCategory.name)
    
    rows = (await db.execute(stmt)).scalars().all()
    
    return [
        {
            "id": cat.id,
            "code": cat.code,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "is_active": cat.is_active,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
        }
        for cat in rows
    ]


@router.post("/categories", response_model=dict)
async def create_post_category(
    payload: PostCategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Tạo danh mục bài viết"""
    # Check if code already exists
    existing_code = await db.execute(
        select(PostCategory).where(PostCategory.code == payload.code)
    )
    if existing_code.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Category code already exists")
    
    # Check if slug already exists
    existing_slug = await db.execute(
        select(PostCategory).where(PostCategory.slug == payload.slug)
    )
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Category slug already exists")
    
    category = PostCategory(
        code=payload.code,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        is_active=True,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


@router.put("/categories/{category_id}", response_model=dict)
async def update_post_category(
    category_id: uuid.UUID,
    payload: PostCategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Cập nhật danh mục bài viết"""
    category = await db.get(PostCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if payload.code is not None and payload.code != category.code:
        existing = await db.execute(
            select(PostCategory).where(PostCategory.code == payload.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Category code already exists")
        category.code = payload.code
    
    if payload.slug is not None and payload.slug != category.slug:
        existing = await db.execute(
            select(PostCategory).where(PostCategory.slug == payload.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Category slug already exists")
        category.slug = payload.slug
    
    if payload.name is not None:
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description
    if payload.is_active is not None:
        category.is_active = payload.is_active
    
    await db.commit()
    await db.refresh(category)
    
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


# ==================== Posts ====================

@router.post("/", response_model=dict)
async def create_post(
    payload: PostCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Tạo bài viết mới"""
    from datetime import datetime
    
    # Generate slug if not provided
    slug = payload.slug
    if not slug:
        slug = payload.title.lower().replace(" ", "-").replace("đ", "d").replace("Đ", "D")
    
    # Check if slug already exists
    existing = await db.execute(
        select(Post).where(Post.slug == slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Post slug already exists")
    
    post = Post(
        category_id=payload.category_id,
        author_user_id=admin_user.id,
        provider_id=payload.provider_id,
        industry_category_id=payload.industry_category_id,
        service_category_id=payload.service_category_id,
        title=payload.title,
        slug=slug,
        summary=payload.summary,
        content=payload.content,
        cover_image_url=payload.cover_image_url,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        post_type=payload.post_type or "article",
        status=payload.status or "draft",
        visibility=payload.visibility or "public",
        is_featured=payload.is_featured or False,
        allow_indexing=payload.allow_indexing if payload.allow_indexing is not None else True,
        published_at=payload.published_at,
        expired_at=payload.expired_at,
        view_count=0,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    return {
        "id": post.id,
        "category_id": post.category_id,
        "author_user_id": post.author_user_id,
        "provider_id": post.provider_id,
        "title": post.title,
        "slug": post.slug,
        "status": post.status,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


@router.get("/")
async def list_posts(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    status: str | None = Query(default=None),
    post_type: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> dict:
    """Danh sách bài viết"""
    conditions = []
    
    if status:
        conditions.append(Post.status == status)
    
    if post_type:
        conditions.append(Post.post_type == post_type)
    
    if category_id:
        conditions.append(Post.category_id == category_id)
    
    if is_featured is not None:
        conditions.append(Post.is_featured == is_featured)
    
    # Base query with joins
    base_stmt = (
        select(Post)
        .outerjoin(PostCategory, Post.category_id == PostCategory.id)
        .outerjoin(User, Post.author_user_id == User.id)
    )
    
    if conditions:
        base_stmt = base_stmt.where(and_(*conditions))
    
    # Count total
    count_stmt = select(1).select_from(Post)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Get paginated results
    stmt = (
        base_stmt
        .order_by(Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    
    result = {
        "items": [],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    
    for post in rows:
        post_data = {
            "id": post.id,
            "category_id": post.category_id,
            "author_user_id": post.author_user_id,
            "provider_id": post.provider_id,
            "title": post.title,
            "slug": post.slug,
            "summary": post.summary,
            "cover_image_url": post.cover_image_url,
            "post_type": post.post_type,
            "status": post.status,
            "visibility": post.visibility,
            "is_featured": post.is_featured,
            "view_count": post.view_count,
            "published_at": post.published_at,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
        }
        
        if post.category:
            post_data["category"] = {
                "id": post.category.id,
                "code": post.category.code,
                "name": post.category.name,
                "slug": post.category.slug,
            }
        
        if post.author:
            post_data["author"] = {
                "id": post.author.id,
                "full_name": post.author.full_name,
                "phone": post.author.phone,
            }
        
        result["items"].append(post_data)
    
    return result


@router.get("/{post_id}", response_model=dict)
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Chi tiết bài viết"""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_data = {
        "id": post.id,
        "category_id": post.category_id,
        "author_user_id": post.author_user_id,
        "provider_id": post.provider_id,
        "industry_category_id": post.industry_category_id,
        "service_category_id": post.service_category_id,
        "title": post.title,
        "slug": post.slug,
        "summary": post.summary,
        "content": post.content,
        "cover_image_url": post.cover_image_url,
        "seo_title": post.seo_title,
        "seo_description": post.seo_description,
        "post_type": post.post_type,
        "status": post.status,
        "visibility": post.visibility,
        "published_at": post.published_at,
        "expired_at": post.expired_at,
        "is_featured": post.is_featured,
        "allow_indexing": post.allow_indexing,
        "view_count": post.view_count,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }
    
    # Add category
    if post.category:
        post_data["category"] = {
            "id": post.category.id,
            "code": post.category.code,
            "name": post.category.name,
            "slug": post.category.slug,
            "description": post.category.description,
        }
    
    # Add author
    if post.author:
        post_data["author"] = {
            "id": post.author.id,
            "full_name": post.author.full_name,
            "phone": post.author.phone,
        }
    
    # Add provider
    if post.provider:
        post_data["provider"] = {
            "id": post.provider.id,
            "provider_type": post.provider.provider_type,
            "status": post.provider.status,
        }
    
    # Add media
    media_result = await db.execute(
        select(PostMedia).where(PostMedia.post_id == post_id).order_by(PostMedia.created_at)
    )
    post_data["media"] = [
        {
            "id": m.id,
            "media_type": m.media_type,
            "file_url": m.file_url,
            "thumbnail_url": m.thumbnail_url,
            "title": m.title,
            "alt_text": m.alt_text,
            "is_active": m.is_active,
            "created_at": m.created_at,
        }
        for m in media_result.scalars().all()
    ]
    
    return post_data


@router.put("/{post_id}", response_model=dict)
async def update_post(
    post_id: uuid.UUID,
    payload: PostUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Cập nhật bài viết"""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Validate slug uniqueness if changed
    if payload.slug is not None and payload.slug != post.slug:
        existing = await db.execute(
            select(Post).where(Post.slug == payload.slug).where(Post.id != post_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Post slug already exists")
    
    # Update fields
    if payload.category_id is not None:
        post.category_id = payload.category_id
    if payload.author_user_id is not None:
        post.author_user_id = payload.author_user_id
    if payload.provider_id is not None:
        post.provider_id = payload.provider_id
    if payload.industry_category_id is not None:
        post.industry_category_id = payload.industry_category_id
    if payload.service_category_id is not None:
        post.service_category_id = payload.service_category_id
    if payload.title is not None:
        post.title = payload.title
    if payload.slug is not None:
        post.slug = payload.slug
    if payload.summary is not None:
        post.summary = payload.summary
    if payload.content is not None:
        post.content = payload.content
    if payload.cover_image_url is not None:
        post.cover_image_url = payload.cover_image_url
    if payload.seo_title is not None:
        post.seo_title = payload.seo_title
    if payload.seo_description is not None:
        post.seo_description = payload.seo_description
    if payload.post_type is not None:
        post.post_type = payload.post_type
    if payload.status is not None:
        post.status = payload.status
    if payload.visibility is not None:
        post.visibility = payload.visibility
    if payload.published_at is not None:
        post.published_at = payload.published_at
    if payload.expired_at is not None:
        post.expired_at = payload.expired_at
    if payload.is_featured is not None:
        post.is_featured = payload.is_featured
    if payload.allow_indexing is not None:
        post.allow_indexing = payload.allow_indexing
    
    await db.commit()
    await db.refresh(post)
    
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "status": post.status,
        "updated_at": post.updated_at,
    }


@router.patch("/{post_id}/status")
async def patch_post_status(
    post_id: uuid.UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
    published_at: Any | None = None,
) -> dict[str, Any]:
    """Cập nhật trạng thái bài viết"""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    valid_statuses = ["draft", "pending_review", "published", "hidden", "archived"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    
    old_status = post.status
    post.status = status
    
    # Set published_at if status is published
    if status == "published" and post.published_at is None:
        from datetime import datetime
        post.published_at = published_at or datetime.now()
    
    await db.commit()
    await db.refresh(post)
    
    return {
        "success": True,
        "post_id": post_id,
        "old_status": old_status,
        "new_status": status,
        "published_at": post.published_at,
    }


from app.schemas.admin import PostMediaCreateRequest as SchemaPostMediaCreateRequest


@router.post("/{post_id}/media", response_model=dict)
async def create_post_media(
    post_id: uuid.UUID,
    payload: SchemaPostMediaCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict:
    """Thêm media vào bài viết"""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    media = PostMedia(
        post_id=post_id,
        media_type=payload.media_type,
        file_url=payload.file_url,
        thumbnail_url=payload.thumbnail_url,
        title=payload.title,
        alt_text=payload.alt_text,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    
    return {
        "id": media.id,
        "media_type": media.media_type,
        "file_url": media.file_url,
        "thumbnail_url": media.thumbnail_url,
        "title": media.title,
        "alt_text": media.alt_text,
        "is_active": media.is_active,
        "created_at": media.created_at,
    }


@router.delete("/post-media/{media_id}")
async def delete_post_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(get_current_admin_user),
) -> dict[str, bool]:
    """Xóa media"""
    media = await db.get(PostMedia, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    db.delete(media)
    await db.commit()
    
    return {"success": True}