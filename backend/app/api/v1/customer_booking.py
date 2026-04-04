from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    FareEstimateRequest,
    FareEstimateResponse,
)
from app.services.booking_service import BookingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Customer / Bookings"], prefix="/customer")

@router.post(
    "/transport/estimate",
    response_model=FareEstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Ước tính cước phí",
    description="Ước tính cước phí trước khi đặt chuyến dựa trên loại dịch vụ và khoảng cách.",
)
async def estimate_fare(
    payload: FareEstimateRequest,
    db: AsyncSession = Depends(get_db),
) -> FareEstimateResponse:
    """Ước tính cước phí trước khi đặt chuyến.

    Args:
        payload: Thông tin yêu cầu gồm service_type, distance_km, duration_min.
        db: Async DB session.

    Returns:
        FareEstimateResponse chứa mức giá ước tính hoặc khoảng giá.
    """
    mode, est_fare, min_q, max_q = await BookingService.calculate_fare(
        db, payload.service_type, payload.distance_km, payload.duration_min
    )
    return FareEstimateResponse(
        service_type=payload.service_type,
        pricing_mode=mode,
        estimated_fare=est_fare,
        min_fare=min_q,
        max_fare=max_q,
    )


@router.post(
    "/transport/booking",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo booking mới",
    description="Khách hàng đặt chuyến vận chuyển. Trả về booking với trạng thái pending và mã OTP lên xe.",
)
async def create_booking(
    payload: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    """Tạo booking mới cho dịch vụ vận chuyển.

    Args:
        payload: Thông tin booking (service_type, pickup/dropoff coords, notes).
        db: Async DB session.
        current_user: Khách hàng đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'pending' và mã OTP lên xe.
    """
    logger.info("[BOOKING] Customer %s creating booking for service %s", current_user.id, payload.service_type)
    booking = await BookingService.create_booking(db, current_user.id, payload)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.get(
    "/transport/booking/{booking_id}",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem trạng thái booking",
    description="Lấy trạng thái hiện tại của booking thuộc về khách hàng đang đăng nhập.",
)
async def get_booking_status(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    """Lấy trạng thái hiện tại của booking.

    Args:
        booking_id: UUID string của booking.
        db: Async DB session.
        current_user: Khách hàng đang đăng nhập.

    Returns:
        BookingResponse chứa trạng thái và thông tin chuyến đi.

    Raises:
        HTTPException 403: Nếu booking không thuộc về customer hiện tại.
        HTTPException 404: Nếu booking không tồn tại.
    """
    booking = await BookingService.get_booking(db, uuid.UUID(booking_id))
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return booking


@router.post(
    "/transport/booking/{booking_id}/cancel",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    summary="Hủy booking",
    description="Khách hàng hủy chuyến đang ở trạng thái pending hoặc accepted.",
)
async def cancel_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    """Khách hàng hủy chuyến.

    Args:
        booking_id: UUID string của booking cần hủy.
        db: Async DB session.
        current_user: Khách hàng đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'cancelled'.

    Raises:
        HTTPException 403: Nếu không phải chủ booking.
        HTTPException 400: Nếu booking không thể hủy ở trạng thái hiện tại.
    """
    logger.info("[BOOKING] Customer %s cancelling booking %s", current_user.id, booking_id)
    booking = await BookingService.cancel_booking(db, uuid.UUID(booking_id), current_user.id)
    await db.commit()
    await db.refresh(booking)
    return booking
