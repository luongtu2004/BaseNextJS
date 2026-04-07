"""Customer Review API — Phase 9.1.

Endpoints:
  POST  /customer/bookings/{id}/review      RV1 — Đánh giá tài xế sau chuyến
  GET   /customer/providers/{id}/reviews    RV2 — Xem đánh giá của provider
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role, get_current_user
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

router = APIRouter(tags=["Customer / Reviews"], prefix="/customer")


# ─────────────────────────────────────────────────────────────────────
# RV1 — Customer đánh giá tài xế
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/bookings/{booking_id}/review",
    response_model=ReviewItem,
    status_code=status.HTTP_201_CREATED,
    summary="Đánh giá tài xế sau chuyến",
    description=(
        "Khách hàng đánh giá tài xế sau khi chuyến hoàn thành. "
        "Mỗi booking chỉ được đánh giá 1 lần."
    ),
)
async def create_review_by_customer(
    booking_id: uuid.UUID,
    payload: CreateReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> ReviewItem:
    """Customer đánh giá tài xế sau chuyến hoàn thành.

    Args:
        booking_id: UUID của booking cần đánh giá.
        payload: Rating (1-5) và comment tùy chọn.
        db: Async DB session.
        current_user: Khách hàng đang đăng nhập.

    Returns:
        ReviewItem chứa review vừa tạo.

    Raises:
        HTTPException 404: Booking không tồn tại.
        HTTPException 403: Booking không thuộc về customer này.
        HTTPException 400: Booking chưa hoàn thành hoặc đã đánh giá rồi.
    """
    # Validate booking
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to review this booking")
    if booking.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot review booking in '{booking.status}' state — must be 'completed'",
        )

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

    # Provider phải có — lấy reviewee_id = provider's user_id
    if not booking.provider_id:
        raise HTTPException(status_code=400, detail="Booking has no assigned provider")
    provider = await db.get(Provider, booking.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    review = Review(
        id=uuid.uuid4(),
        booking_id=booking_id,
        reviewer_id=current_user.id,
        reviewee_id=provider.user_id,
        reviewer_role="customer",
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    logger.info(
        "[REVIEW] Customer %s rated provider %s -> %d stars (booking %s)",
        current_user.id,
        provider.user_id,
        payload.rating,
        booking_id,
    )
    return ReviewItem.model_validate(review)


# ─────────────────────────────────────────────────────────────────────
# RV2 — Xem đánh giá của provider
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/providers/{provider_id}/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem đánh giá của provider",
    description="Danh sách đánh giá mà khách hàng đã gửi cho một provider, sắp xếp theo thời gian mới nhất.",
)
async def list_provider_reviews(
    provider_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item mỗi trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewListResponse:
    """Danh sách đánh giá của provider (paginated).

    Chỉ trả về review có is_visible=True.

    Args:
        provider_id: UUID của provider.
        page: Trang hiện tại.
        page_size: Số item mỗi trang.
        db: Async DB session.
        current_user: User đang đăng nhập (customer hoặc provider).

    Returns:
        ReviewListResponse với pagination.

    Raises:
        HTTPException 404: Provider không tồn tại.
    """
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    base_stmt = select(Review).where(
        Review.reviewee_id == provider.user_id,
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
