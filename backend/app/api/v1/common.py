from __future__ import annotations

import logging
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
from app.schemas.identity import (
    IdentityFileResponse,
    IdentityVerificationCreate,
    IdentityVerificationDetailResponse,
    IdentityVerificationResponse,
    IdentityVerificationStatusResponse,
)
from app.models.identity import UserIdentityFile, UserIdentityVerification
from fastapi import UploadFile, File, Form

logger = logging.getLogger(__name__)

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
    logger.info("Profile updated - user_id=%s", current_user.id)

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


@router.get("/me/verification-status", response_model=IdentityVerificationStatusResponse)
async def get_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return IdentityVerificationStatusResponse(
        identity_verification_status=current_user.identity_verification_status,
        identity_verified_at=current_user.identity_verified_at,
        latest_identity_verification_id=current_user.latest_identity_verification_id,
    )


@router.get("/me/identity-verifications", response_model=list[IdentityVerificationResponse])
async def list_identity_verifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserIdentityVerification)
        .where(UserIdentityVerification.user_id == current_user.id)
        .order_by(UserIdentityVerification.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.post("/me/identity-verifications", response_model=IdentityVerificationResponse)
async def create_identity_verification(
    payload: IdentityVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id,
        UserIdentityVerification.status.in_(["draft", "submitted", "processing"]),
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Bạn đang có một hồ sơ xác minh chưa hoàn thành hoặc đang được xử lý."
        )

    update_stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.user_id == current_user.id, UserIdentityVerification.is_latest == True
    )
    latest_rows = (await db.execute(update_stmt)).scalars().all()
    for row in latest_rows:
        row.is_latest = False

    new_ver = UserIdentityVerification(
        user_id=current_user.id,
        verification_type=payload.verification_type,
        status="draft",
        review_mode="hybrid",
        is_latest=True,
    )
    db.add(new_ver)
    current_user.latest_identity_verification_id = new_ver.id

    await db.commit()
    await db.refresh(new_ver)
    logger.info("Identity verification created - user_id=%s verification_id=%s type=%s",
                current_user.id, new_ver.id, payload.verification_type)
    return new_ver


@router.get(
    "/me/identity-verifications/{id}", response_model=IdentityVerificationDetailResponse
)
async def get_identity_verification_detail(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.id == id,
        UserIdentityVerification.user_id == current_user.id,
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")

    files_stmt = select(UserIdentityFile).where(UserIdentityFile.verification_id == id)
    files = (await db.execute(files_stmt)).scalars().all()

    response = IdentityVerificationDetailResponse.model_validate(record)
    response.files = [IdentityFileResponse.model_validate(f) for f in files]
    return response


@router.post(
    "/me/identity-verifications/{id}/files", response_model=IdentityFileResponse
)
async def upload_identity_verification_file(
    id: uuid.UUID,
    file_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.id == id,
        UserIdentityVerification.user_id == current_user.id,
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    if record.status != "draft":
        raise HTTPException(
            status_code=400, detail="Chỉ có thể tải lên tài liệu khi hồ sơ ở trạng thái draft."
        )

    file_url = f"/uploads/{uuid.uuid4()}_{file.filename}"

    new_file = UserIdentityFile(
        verification_id=record.id,
        file_type=file_type,
        file_url=file_url,
        uploaded_by_user_id=current_user.id,
        mime_type=file.content_type,
        file_size=file.size,
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file


@router.post("/me/identity-verifications/{id}/submit")
async def submit_identity_verification(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.id == id,
        UserIdentityVerification.user_id == current_user.id,
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    if record.status != "draft":
        raise HTTPException(
            status_code=400, detail="Chỉ có thể nộp hồ sơ khi đang ở trạng thái draft."
        )

    files_stmt = select(UserIdentityFile).where(UserIdentityFile.verification_id == id)
    files = (await db.execute(files_stmt)).scalars().all()
    file_types = {f.file_type for f in files}

    if record.verification_type == "cccd":
        if "id_front" not in file_types or "id_back" not in file_types or "selfie" not in file_types:
            raise HTTPException(
                status_code=400, detail="Thiếu ảnh CCCD mặt trước, mặt sau hoặc ảnh selfie."
            )

    record.status = "submitted"
    record.submitted_at = func.now()
    current_user.identity_verification_status = "pending"

    await db.commit()
    logger.info("Identity verification submitted - verification_id=%s user_id=%s", id, current_user.id)
    return {"id": record.id, "status": "submitted"}


@router.post("/me/identity-verifications/{id}/cancel")
async def cancel_identity_verification(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIdentityVerification).where(
        UserIdentityVerification.id == id,
        UserIdentityVerification.user_id == current_user.id,
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    if record.status not in ["draft", "submitted"]:
        raise HTTPException(
            status_code=400, detail="Không thể hủy hồ sơ ở trạng thái hiện tại."
        )

    record.status = "cancelled"

    stmt_last = (
        select(UserIdentityVerification)
        .where(
            UserIdentityVerification.user_id == current_user.id,
            UserIdentityVerification.id != id,
            UserIdentityVerification.status.in_(["approved", "rejected"]),
        )
        .order_by(UserIdentityVerification.created_at.desc())
        .limit(1)
    )

    last_valid = (await db.execute(stmt_last)).scalar_one_or_none()
    if last_valid:
        if last_valid.status == "approved":
            current_user.identity_verification_status = "verified"
            current_user.latest_identity_verification_id = last_valid.id
            last_valid.is_latest = True
        elif last_valid.status == "rejected":
            current_user.identity_verification_status = "rejected"
            current_user.latest_identity_verification_id = last_valid.id
            last_valid.is_latest = True
    else:
        current_user.identity_verification_status = "unverified"
        current_user.latest_identity_verification_id = None

    await db.commit()
    logger.info("Identity verification cancelled - verification_id=%s user_id=%s", id, current_user.id)
    return {"id": record.id, "status": "cancelled"}
