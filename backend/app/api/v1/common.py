from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select, update as sa_update
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
from app.models.identity import UserIdentityFile, UserIdentityVerification, UserIdentityVerificationLog
from app.models.notification import Notification, NotificationSetting
from app.schemas.notification import (
    NotificationItem,
    NotificationListResponse,
    NotificationSettingItem,
    NotificationSettingsResponse,
    UnreadCountResponse,
    UpdateNotificationSettingsRequest,
    VALID_NOTIFICATION_TYPES,
)
from app.services.ai_service import AIService
from app.core.config import get_settings
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
    file_map = {f.file_type: f.file_url for f in files}

    # THỨ TỰ CHECK:
    # 1. Kiểm tra đủ file (Group A - Quality check cơ bản)
    if record.verification_type == "cccd":
        required = ["id_front", "id_back", "selfie"]
        missing = [rt for rt in required if rt not in file_map]
        if missing:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "missing_required_files", "message": f"Thiếu tài liệu: {', '.join(missing)}"}
            )

    # 2. GIAO AI KIỂM TRA (OCR, FACE MATCH, LIVENESS, QUALITY)
    settings = get_settings()
    ai_result = await AIService.verify_identity(file_map)
    
    # 2.1 LOG kết quả thô của AI
    for step in ["quality", "ocr", "face_match", "liveness"]:
        step_data = ai_result.get(step, {})
        new_log = UserIdentityVerificationLog(
            verification_id=id,
            step_name=step,
            provider_name="AI_SERVICE_INTERNAL",
            response_payload_json=step_data,
            status="success" if step_data.get("status") == "success" else "failed",
            score=step_data.get("score") or step_data.get("confidence"),
            error_code=step_data.get("error_code")
        )
        db.add(new_log)

    # 3. QUY TẮC PHÂN LOẠI (DECISION MATRIX)
    quality = ai_result.get("quality", {})
    ocr = ai_result.get("ocr", {})
    face_match = ai_result.get("face_match", {})
    liveness = ai_result.get("liveness", {})

    # 3.1 Nhóm A (Chất lượng ảnh/Loại giấy tờ) -> Nếu fail thì giữ Draft, trả lỗi bắt chụp lại ngay
    if (quality.get("is_blur") or quality.get("is_glare") or 
        quality.get("is_cropped") or quality.get("is_wrong_side") or
        ocr.get("status") == "failed"):
        
        detail = {"error_code": "image_quality_failed", "message": "Ảnh mờ, lóa hoặc sai mặt. Vui lòng chụp lại."}
        if quality.get("is_wrong_side"): detail["error_code"] = "wrong_document_side"
        if ocr.get("status") == "failed": detail["error_code"] = "ocr_unreadable"
        
        # Vẫn submit log nhưng không đổi status của record -> giữ draft
        await db.commit()
        raise HTTPException(status_code=400, detail=detail)

    # 3.2 Cập nhật data chi tiết từ OCR
    ocr_data = ocr.get("data", {})
    record.full_name_on_id = ocr_data.get("full_name")
    record.id_number = ocr_data.get("id_number")
    record.date_of_birth_on_id = date.fromisoformat(ocr_data.get("dob")) if ocr_data.get("dob") else None
    record.issue_date = date.fromisoformat(ocr_data.get("issue_date")) if ocr_data.get("issue_date") else None
    record.expiry_date = date.fromisoformat(ocr_data.get("expiry_date")) if ocr_data.get("expiry_date") else None
    record.ocr_confidence = ocr.get("confidence")
    record.face_match_score = face_match.get("score")
    record.liveness_score = liveness.get("score")

    # 3.3 QUYẾT ĐỊNH CUỐI CÙNG
    # Auto Approve nếu tất cả đều trên ngưỡng
    all_pass = (
        (ocr.get("confidence") or 0) >= settings.ocr_confidence_threshold and
        (face_match.get("score") or 0) >= settings.face_match_threshold and
        (liveness.get("score") or 0) >= settings.liveness_threshold
    )

    record.submitted_at = func.now()

    if all_pass:
        record.status = "approved"
        record.processed_at = func.now()
        record.review_mode = "auto"
        current_user.identity_verification_status = "verified"
        current_user.identity_verified_at = func.now()
        msg = "Xác minh tự động thành công."
    else:
        # Chuyển Admin Review nếu ảnh OK nhưng điểm thấp hoặc nghi vấn
        record.status = "processing"
        record.review_mode = "hybrid"
        current_user.identity_verification_status = "processing"
        msg = "Hồ sơ đang được chuyển admin kiểm tra thêm."

    await db.commit()
    logger.info("Identity verification %s - id=%s user_id=%s", record.status, id, current_user.id)
    return {"id": record.id, "status": record.status, "message": msg}


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


# ═════════════════════════════════════════════════════════════════════
# Phase 9.2 — Notifications (NF1-NF6)
# ═════════════════════════════════════════════════════════════════════




# ─────────────────────────────────────────────────────────────────────
# NF1 — Danh sách thông báo
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/me/notifications",
    response_model=NotificationListResponse,
    summary="Danh sách thông báo",
    description="Lấy danh sách thông báo của user hiện tại, sắp xếp theo thời gian mới nhất.",
)
async def list_my_notifications(
    is_read: bool | None = Query(default=None, description="Lọc theo trạng thái đọc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    """Danh sách thông báo in-app của user (paginated).

    Args:
        is_read: Lọc theo trạng thái đọc — True (đã đọc), False (chưa đọc), None (tất cả).
        page: Trang hiện tại.
        page_size: Số item mỗi trang (tối đa 100).
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        NotificationListResponse với danh sách và pagination.
    """
    base_stmt = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        base_stmt = base_stmt.where(Notification.is_read.is_(is_read))

    total = (
        await db.execute(select(func.count()).select_from(base_stmt.subquery()))
    ).scalar_one()

    items = (
        await db.execute(
            base_stmt.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return NotificationListResponse(
        items=[NotificationItem.model_validate(n) for n in items],
        page=page,
        page_size=page_size,
        total=total,
    )


# ─────────────────────────────────────────────────────────────────────
# NF2 — Đánh dấu một thông báo đã đọc
# ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/me/notifications/{notification_id}/read",
    response_model=NotificationItem,
    summary="Đánh dấu đã đọc",
    description="Đánh dấu một thông báo cụ thể là đã đọc.",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationItem:
    """Đánh dấu một thông báo là đã đọc.

    Args:
        notification_id: UUID của thông báo cần đánh dấu.
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        NotificationItem đã cập nhật is_read=True.

    Raises:
        HTTPException 404: Thông báo không tồn tại hoặc không thuộc user.
    """
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(tz=timezone.utc)
        await db.commit()
        await db.refresh(notification)

    return NotificationItem.model_validate(notification)


# ─────────────────────────────────────────────────────────────────────
# NF3 — Đánh dấu tất cả đã đọc
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/me/notifications/read-all",
    response_model=dict,
    summary="Đánh dấu tất cả đã đọc",
    description="Đánh dấu tất cả thông báo chưa đọc của user hiện tại là đã đọc.",
)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Đánh dấu tất cả thông báo chưa đọc là đã đọc.

    Args:
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        Dict với updated_count — số thông báo đã được cập nhật.
    """
    now = datetime.now(tz=timezone.utc)
    result = await db.execute(
        sa_update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=now)
    )
    await db.commit()
    updated = result.rowcount
    logger.info("[NOTIFICATION] User %s marked %d notifications as read", current_user.id, updated)
    return {"updated_count": updated}


# ─────────────────────────────────────────────────────────────────────
# NF4 — Unread count (badge)
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/me/notifications/unread-count",
    response_model=UnreadCountResponse,
    summary="Số thông báo chưa đọc",
    description="Trả về số thông báo chưa đọc — dùng để hiển thị badge icon trên app.",
)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    """Đếm số thông báo chưa đọc của user.

    Args:
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        UnreadCountResponse với count.
    """
    count = (
        await db.execute(
            select(func.count()).where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
    ).scalar_one()
    return UnreadCountResponse(count=count)


# ─────────────────────────────────────────────────────────────────────
# NF5 — Xem notification settings
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/me/notification-settings",
    response_model=NotificationSettingsResponse,
    summary="Xem cấu hình nhận thông báo",
    description="Trả về danh sách toàn bộ loại thông báo và trạng thái on/off của từng loại.",
)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationSettingsResponse:
    """Xem cấu hình thông báo của user.

    Trả về tất cả VALID_NOTIFICATION_TYPES với trạng thái is_enabled.
    Nếu chưa có record cho type nào → mặc định True.

    Args:
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        NotificationSettingsResponse với danh sách settings.
    """
    rows = (
        await db.execute(
            select(NotificationSetting).where(
                NotificationSetting.user_id == current_user.id
            )
        )
    ).scalars().all()

    settings_map = {r.notification_type: r.is_enabled for r in rows}

    settings = [
        NotificationSettingItem(
            notification_type=ntype,
            is_enabled=settings_map.get(ntype, True),  # default: enabled
        )
        for ntype in sorted(VALID_NOTIFICATION_TYPES)
    ]
    return NotificationSettingsResponse(settings=settings)


# ─────────────────────────────────────────────────────────────────────
# NF6 — Cập nhật notification settings
# ─────────────────────────────────────────────────────────────────────


@router.put(
    "/me/notification-settings",
    response_model=NotificationSettingsResponse,
    summary="Cập nhật cấu hình thông báo",
    description="Batch update on/off từng loại thông báo. Ghi đè (upsert) từng type được truyền lên.",
)
async def update_notification_settings(
    payload: UpdateNotificationSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationSettingsResponse:
    """Cập nhật cấu hình nhận thông báo — upsert theo từng type.

    Chỉ các types trong VALID_NOTIFICATION_TYPES mới được chấp nhận.
    Không truyền type nào → type đó giữ nguyên giá trị cũ.

    Args:
        payload: Danh sách settings cần cập nhật.
        db: Async DB session.
        current_user: User đang đăng nhập.

    Returns:
        NotificationSettingsResponse với toàn bộ settings sau khi cập nhật.

    Raises:
        HTTPException 400: Nếu notification_type không hợp lệ.
    """
    now = datetime.now(tz=timezone.utc)

    for item in payload.settings:
        if item.notification_type not in VALID_NOTIFICATION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification_type: '{item.notification_type}'. "
                       f"Valid: {sorted(VALID_NOTIFICATION_TYPES)}",
            )

    for item in payload.settings:
        existing = (
            await db.execute(
                select(NotificationSetting).where(
                    NotificationSetting.user_id == current_user.id,
                    NotificationSetting.notification_type == item.notification_type,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.is_enabled = item.is_enabled
            existing.updated_at = now
        else:
            db.add(
                NotificationSetting(
                    id=uuid.uuid4(),
                    user_id=current_user.id,
                    notification_type=item.notification_type,
                    is_enabled=item.is_enabled,
                )
            )

    await db.commit()
    logger.info(
        "[NOTIFICATION] User %s updated %d notification settings",
        current_user.id,
        len(payload.settings),
    )

    # Return full settings after update
    return await get_notification_settings(db=db, current_user=current_user)
