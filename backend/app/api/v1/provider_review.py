"""Provider Review API — Phase 9.1.

Endpoints:
  POST  /provider/bookings/{id}/review    PRV1 — Tài xế đánh giá khách sau chuyến
  GET   /provider/me/reviews              PRV2 — Xem đánh giá mình nhận được
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.review import Review
from app.models.user import User
from app.schemas.review import (
    CreateReviewRequest,
    ReviewItem,
    ReviewListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Provider / Reviews"], prefix="/provider")


# ─────────────────────────────────────────────────────────────────────
# PRV1 — Provider đánh giá khách
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/bookings/{booking_id}/review",
    response_model=ReviewItem,
    status_code=status.HTTP_201_CREATED,
    summary="Đánh giá khách sau chuyến",
    description="Tài xế đánh giá khách hàng sau khi chuyến hoàn thành. Mỗi booking chỉ được đánh giá 1 lần.",
)
async def create_review_by_provider(
    booking_id: uuid.UUID,
    payload: CreateReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider")),
) -> ReviewItem:
    """Tài xế đánh giá khách hàng sau chuyến hoàn thành.

    Args:
        booking_id: UUID của booking cần đánh giá.
        payload: Rating (1-5) và comment tùy chọn.
        db: Async DB session.
        current_user: Tài xế đang đăng nhập.

    Returns:
        ReviewItem chứa review vừa tạo.

    Raises:
        HTTPException 404: Booking không tồn tại.
        HTTPException 403: Booking không phải của provider này.
        HTTPException 400: Booking chưa hoàn thành hoặc đã đánh giá rồi.
    """
    # Validate booking
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot review booking in '{booking.status}' state — must be 'completed'",
        )

    # Validate ownership — provider phải là người thực hiện chuyến
    provider = (
        await db.execute(
            select(Provider).where(Provider.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=403, detail="Provider profile not found")
    if booking.provider_id != provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to review this booking")

    # Check: chưa đánh giá lần nào
    existing = (
        await db.execute(
            select(Review).where(
                Review.booking_id == booking_id,
                Review.reviewer_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this booking"
        )

    review = Review(
        id=uuid.uuid4(),
        booking_id=booking_id,
        reviewer_id=current_user.id,
        reviewee_id=booking.customer_id,
        reviewer_role="provider",
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    logger.info(
        "[REVIEW] Provider %s rated customer %s -> %d stars (booking %s)",
        current_user.id,
        booking.customer_id,
        payload.rating,
        booking_id,
    )
    return ReviewItem.model_validate(review)


# ─────────────────────────────────────────────────────────────────────
# PRV2 — Tài xế xem đánh giá nhận được
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/me/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem đánh giá mình nhận được",
    description="Tài xế xem danh sách đánh giá khách hàng gửi cho mình, sắp xếp theo thời gian mới nhất.",
)
async def list_my_reviews(
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item mỗi trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider")),
) -> ReviewListResponse:
    """Tài xế xem danh sách đánh giá của chính mình (paginated).

    Chỉ trả về review có is_visible=True từ khách hàng (reviewer_role='customer').

    Args:
        page: Trang hiện tại.
        page_size: Số item mỗi trang (tối đa 100).
        db: Async DB session.
        current_user: Tài xế đang đăng nhập.

    Returns:
        ReviewListResponse với pagination.
    """
    base_stmt = select(Review).where(
        Review.reviewee_id == current_user.id,
        Review.reviewer_role == "customer",
        Review.is_visible.is_(True),
    )

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
