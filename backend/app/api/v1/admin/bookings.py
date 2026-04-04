"""Admin API — Quản lý Booking & Orders (Phase 7).

Endpoints:
  GET    /admin/bookings               Danh sách tất cả booking (filter + pagination)
  GET    /admin/bookings/{id}          Chi tiết booking + status log
  PATCH  /admin/bookings/{id}/cancel   Admin force-cancel booking
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.booking import Booking, BookingStatusLog
from app.models.user import User
from app.schemas.booking import BookingResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin / Bookings"])


# ─────────────────────────────────────────────────────────────────────
# List
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/bookings",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Danh sách booking",
    description="Admin xem danh sách tất cả booking, hỗ trợ filter theo status/service_type/customer/provider.",
)
async def admin_list_bookings(
    status: str | None = Query(default=None, description="Lọc theo trạng thái booking"),
    service_type: str | None = Query(default=None, description="Lọc theo loại dịch vụ"),
    customer_id: uuid.UUID | None = Query(default=None, description="Lọc theo customer"),
    provider_id: uuid.UUID | None = Query(default=None, description="Lọc theo provider"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> dict:
    """Danh sách tất cả booking. Hỗ trợ filter theo status, service_type, customer, provider.

    Args:
        status: Trạng thái booking (pending/accepted/arrived/boarded/completed/cancelled).
        service_type: Mã loại dịch vụ.
        customer_id: UUID khách hàng.
        provider_id: UUID provider.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        Dict phân trang chứa items (BookingResponse), page, page_size, total.
    """
    base_stmt = select(Booking)
    if status:
        base_stmt = base_stmt.where(Booking.status == status)
    if service_type:
        base_stmt = base_stmt.where(Booking.service_type == service_type)
    if customer_id:
        base_stmt = base_stmt.where(Booking.customer_id == customer_id)
    if provider_id:
        base_stmt = base_stmt.where(Booking.provider_id == provider_id)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(Booking.requested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    bookings = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [BookingResponse.model_validate(b) for b in bookings],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


# ─────────────────────────────────────────────────────────────────────
# Detail
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/bookings/{booking_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết booking",
    description="Admin xem chi tiết booking kèm toàn bộ lịch sử trạng thái.",
)
async def admin_get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> dict:
    """Chi tiết booking kèm toàn bộ lịch sử trạng thái.

    Args:
        booking_id: UUID của booking.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        Dict gồm booking (BookingResponse) và status_logs.

    Raises:
        HTTPException 404: Nếu booking không tồn tại.
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    logs = (
        await db.execute(
            select(BookingStatusLog)
            .where(BookingStatusLog.booking_id == booking_id)
            .order_by(BookingStatusLog.created_at)
        )
    ).scalars().all()

    return {
        "booking": BookingResponse.model_validate(booking),
        "status_logs": [
            {
                "id": str(log.id),
                "from_status": log.from_status,
                "to_status": log.to_status,
                "changed_by": str(log.changed_by) if log.changed_by else None,
                "note": log.note,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


# ─────────────────────────────────────────────────────────────────────
# Force Cancel
# ─────────────────────────────────────────────────────────────────────

@router.patch(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    summary="Force-cancel booking",
    description="Admin buộc hủy bất kỳ booking nào chưa hoàn thành. Dùng để giải quyết tranh chấp.",
)
async def admin_cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> BookingResponse:
    """Admin force-cancel bất kỳ booking nào chưa hoàn thành.

    Dùng để giải quyết tranh chấp hoặc xử lý vi phạm.

    Args:
        booking_id: UUID của booking cần hủy.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'cancelled'.

    Raises:
        HTTPException 404: Nếu booking không tồn tại.
        HTTPException 400: Nếu booking đã hoàn thành hoặc đã bị hủy.
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel booking in '{booking.status}' state",
        )

    old_status = booking.status
    booking.status = "cancelled"
    booking.cancelled_at = datetime.now(tz=timezone.utc)
    booking.cancelled_by = "admin"

    log = BookingStatusLog(
        id=uuid.uuid4(),
        booking_id=booking.id,
        from_status=old_status,
        to_status="cancelled",
        changed_by=current_admin.id,
        note="Admin force-cancelled booking",
    )
    db.add(log)
    await db.commit()
    await db.refresh(booking)

    logger.info("[ADMIN] Booking %s force-cancelled by admin %s", booking_id, current_admin.id)
    return booking
