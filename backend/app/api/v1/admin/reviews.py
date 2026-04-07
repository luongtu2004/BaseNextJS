"""Admin Review API — Phase 9.1.

Endpoints:
  GET    /admin/reviews              ARV1 — Toàn bộ đánh giá + filter
  PATCH  /admin/reviews/{id}/visibility  ARV2 — Ẩn/hiện đánh giá vi phạm
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewItem, ReviewListResponse, ReviewVisibilityUpdate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin / Reviews"])


# ─────────────────────────────────────────────────────────────────────
# ARV1 — Danh sách reviews
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="Danh sách tất cả đánh giá",
    description="Admin xem toàn bộ đánh giá, hỗ trợ filter và phân trang.",
)
async def admin_list_reviews(
    reviewer_role: str | None = Query(
        default=None,
        description="Lọc theo vai trò người đánh giá: 'customer' | 'provider'",
    ),
    rating: int | None = Query(
        default=None, ge=1, le=5, description="Lọc theo số sao"
    ),
    is_visible: bool | None = Query(
        default=None, description="Lọc theo trạng thái hiển thị"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> ReviewListResponse:
    """Admin xem toàn bộ đánh giá với filter linh hoạt.

    Args:
        reviewer_role: Lọc theo vai trò người đánh giá ('customer' / 'provider').
        rating: Lọc theo số sao (1-5).
        is_visible: Lọc theo trạng thái hiển thị.
        page: Trang hiện tại.
        page_size: Số item mỗi trang (tối đa 200).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        ReviewListResponse với pagination.
    """
    base_stmt = select(Review)
    if reviewer_role:
        base_stmt = base_stmt.where(Review.reviewer_role == reviewer_role)
    if rating is not None:
        base_stmt = base_stmt.where(Review.rating == rating)
    if is_visible is not None:
        base_stmt = base_stmt.where(Review.is_visible.is_(is_visible))

    total = (
        await db.execute(select(func.count()).select_from(base_stmt.subquery()))
    ).scalar_one()

    items = (
        await db.execute(
            base_stmt.order_by(Review.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return ReviewListResponse(
        items=[ReviewItem.model_validate(r) for r in items],
        page=page,
        page_size=page_size,
        total=total,
    )


# ─────────────────────────────────────────────────────────────────────
# ARV2 — Toggle visibility
# ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/reviews/{review_id}/visibility",
    response_model=ReviewItem,
    status_code=status.HTTP_200_OK,
    summary="Ẩn/hiện đánh giá vi phạm",
    description="Admin ẩn hoặc bật lại hiển thị của review. Review không bị xóa khỏi DB.",
)
async def admin_toggle_review_visibility(
    review_id: uuid.UUID,
    payload: ReviewVisibilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> ReviewItem:
    """Admin toggle is_visible của review — dùng để xử lý nội dung vi phạm.

    Review vẫn tồn tại trong DB, chỉ ẩn khỏi hiển thị công khai.

    Args:
        review_id: UUID của review cần cập nhật.
        payload: is_visible = True (hiển thị) hoặc False (ẩn).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        ReviewItem với is_visible đã cập nhật.

    Raises:
        HTTPException 404: Review không tồn tại.
    """
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    old_visible = review.is_visible
    review.is_visible = payload.is_visible
    await db.commit()
    await db.refresh(review)

    logger.info(
        "[REVIEW] Admin %s changed review %s visibility: %s → %s",
        current_admin.id,
        review_id,
        old_visible,
        payload.is_visible,
    )
    return ReviewItem.model_validate(review)
