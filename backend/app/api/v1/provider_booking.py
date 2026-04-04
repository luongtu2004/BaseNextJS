from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, check_user_role
from app.db.session import get_db
from app.models.booking import Booking, DriverAvailabilitySession, DriverLocation
from app.models.provider import Provider
from app.models.user import User
from app.schemas.booking import (
    BookingProviderResponse,
    BookingResponse,
    BookingSummaryResponse,
    DriverAvailabilitySessionResponse,
    DriverLocationUpdate,
    DriverLocationResponse,
    DriverSessionCreate,
)
from app.services.booking_service import BookingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────────────────────────────

async def get_provider_user(
    current_user: User = Depends(check_user_role("provider")),
) -> User:
    """Dependency: validate role 'provider'."""
    return current_user


async def _get_provider_or_400(current_user: User, db: AsyncSession) -> Provider:
    """Lấy Provider profile của user hiện tại hoặc raise 400.

    Args:
        current_user: User đang đăng nhập với role provider.
        db: Async DB session.

    Returns:
        Provider record thuộc về current_user.

    Raises:
        HTTPException 400: Nếu user chưa có profile provider.
    """
    provider = (
        await db.execute(select(Provider).where(Provider.owner_user_id == current_user.id))
    ).scalars().first()

    if not provider:
        logger.warning("[PROVIDER] Profile not found for user %s", current_user.id)
        raise HTTPException(status_code=400, detail="Provider profile not found for user")
    return provider


# ─────────────────────────────────────────────────────────────────────
# Booking: Browse & Lifecycle
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/available",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Danh sách cuốc xe chờ",
    description="Trả về danh sách booking pending mà tài xế có thể nhận. OTP không được trả về trong response này.",
)
async def list_available_bookings(
    service_type: str | None = None,
    page: int = Query(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> dict:
    """Danh sách các cuốc xe đang chờ nhận.

    Tài xế dùng API này để duyệt các booking `pending`. MVP hiện tại đơn giản
    trả về danh sách cuốc chờ theo `service_type`. Tương lai (Phase 8) có thể
    áp dụng geospacial filtering theo bán kính 5km.

    Args:
        service_type: Lọc theo loại dịch vụ.
        page: Số trang hiện tại.
        page_size: Số mục trên mỗi trang.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        Dict phân trang chứa danh sách items (BookingSummaryResponse — không có OTP),
        page, page_size, total.
    """
    logger.info("[BOOKING] Provider %s browsing available bookings", current_user.id)

    base_query = select(Booking).where(Booking.status == "pending")
    if service_type:
        base_query = base_query.where(Booking.service_type == service_type)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    query = (
        base_query
        .order_by(Booking.requested_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    result = await db.execute(query)
    bookings = result.scalars().all()

    return {
        "items": [BookingSummaryResponse.model_validate(b) for b in bookings],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/{id}/accept",
    response_model=BookingProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Nhận cuốc xe",
    description="Tài xế nhận cuốc xe đang ở trạng thái pending.",
)
async def accept_booking(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> BookingProviderResponse:
    """Tài xế nhận cuốc xe.

    Args:
        id: UUID của booking cần nhận.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'accepted'.

    Raises:
        HTTPException 400: Nếu không tìm thấy profile tài xế, hoặc booking không ở trạng thái pending.
    """
    logger.info("[BOOKING] Provider %s accepting booking %s", current_user.id, id)
    provider = await _get_provider_or_400(current_user, db)
    booking = await BookingService.accept_booking(db, id, provider.id)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post(
    "/{id}/arrive",
    response_model=BookingProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Xác nhận đến điểm đón",
    description="Tài xế xác nhận đã đến điểm đón khách.",
)
async def arrive_at_pickup(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> BookingProviderResponse:
    """Xác nhận tài xế đã đến điểm đón khách.

    Args:
        id: UUID của booking.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'arrived'.

    Raises:
        HTTPException 400: Nếu không tìm thấy profile tài xế.
    """
    logger.info("[BOOKING] Provider %s arrived at pickup for booking %s", current_user.id, id)
    provider = await _get_provider_or_400(current_user, db)
    booking = await BookingService.update_trip_state(db, id, provider.id, action="arrive")
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post(
    "/{id}/board",
    response_model=BookingProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Hành khách lên xe",
    description="Xác nhận hành khách lên xe bằng OTP. OTP do khách cung cấp và có hiệu lực 30 phút.",
)
async def passenger_board(
    id: uuid.UUID,
    otp: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> BookingProviderResponse:
    """Hành khách lên xe (yêu cầu mã OTP).

    Args:
        id: UUID của booking.
        otp: Mã OTP cung cấp bởi khách hàng để xác thực.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'boarded'.

    Raises:
        HTTPException 400: Nếu OTP sai hoặc sai luồng lifecycle.
    """
    logger.info("[BOOKING] Provider %s verifying boarding OTP for booking %s", current_user.id, id)
    provider = await _get_provider_or_400(current_user, db)
    booking = await BookingService.update_trip_state(db, id, provider.id, action="board", otp=otp)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post(
    "/{id}/complete",
    response_model=BookingProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Hoàn thành chuyến đi",
    description="Tài xế xác nhận kết thúc chuyến đi và thả khách an toàn.",
)
async def complete_trip(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> BookingProviderResponse:
    """Tài xế xác nhận kết thúc chuyến đi và thả khách an toàn.

    Args:
        id: UUID của booking.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        BookingResponse với trạng thái 'completed'.
    """
    logger.info("[BOOKING] Provider %s completing trip %s", current_user.id, id)
    provider = await _get_provider_or_400(current_user, db)
    booking = await BookingService.update_trip_state(db, id, provider.id, action="complete")
    await db.commit()
    await db.refresh(booking)
    return booking


# ─────────────────────────────────────────────────────────────────────
# Provider Availability & Location
# ─────────────────────────────────────────────────────────────────────

@router.post(
    "/availability/online",
    response_model=DriverAvailabilitySessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Bật trạng thái online",
    description="Tài xế chuyển sang trạng thái online để nhận cuốc xe.",
)
async def go_online(
    body: DriverSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> DriverAvailabilitySessionResponse:
    """Tài xế chuyển sang trạng thái online để nhận cuốc xe.

    Nếu đã có session trước đó: cập nhật lại status và online_at.
    Nếu chưa có: tạo session mới.

    Args:
        body: Thông tin session (vehicle_id tuỳ chọn).
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        DriverAvailabilitySessionResponse với status='online'.
    """
    logger.info("[PROVIDER] User %s going online", current_user.id)
    provider = await _get_provider_or_400(current_user, db)

    stmt = select(DriverAvailabilitySession).where(DriverAvailabilitySession.provider_id == provider.id)
    session = (await db.execute(stmt)).scalars().first()
    now_utc = datetime.now(tz=timezone.utc)

    if not session:
        session = DriverAvailabilitySession(
            provider_id=provider.id,
            vehicle_id=body.vehicle_id,
            status="online",
            online_at=now_utc,
            offline_at=None,
        )
        db.add(session)
    else:
        session.status = "online"
        session.vehicle_id = body.vehicle_id
        session.online_at = now_utc
        session.offline_at = None

    await db.commit()
    await db.refresh(session)
    return session


@router.post(
    "/availability/offline",
    response_model=DriverAvailabilitySessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Tắt trạng thái online",
    description="Tài xế chuyển sang trạng thái offline, ngừng nhận cuốc.",
)
async def go_offline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> DriverAvailabilitySessionResponse:
    """Tài xế chuyển sang trạng thái offline.

    Args:
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        DriverAvailabilitySessionResponse với status='offline'.

    Raises:
        HTTPException 400: Nếu không có session nào đang hoạt động.
    """
    logger.info("[PROVIDER] User %s going offline", current_user.id)
    provider = await _get_provider_or_400(current_user, db)

    stmt = select(DriverAvailabilitySession).where(DriverAvailabilitySession.provider_id == provider.id)
    session = (await db.execute(stmt)).scalars().first()

    if not session:
        raise HTTPException(status_code=400, detail="No active session found")

    session.status = "offline"
    session.offline_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(session)
    return session


@router.post(
    "/location",
    response_model=DriverLocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật vị trí",
    description="Tài xế gửi vị trí GPS hiện tại (heartbeat). Upsert: tạo mới hoặc cập nhật bản ghi hiện có.",
)
async def ping_location(
    body: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> DriverLocationResponse:
    """Cập nhật vị trí thời gian thực của tài xế (heartbeat).

    Upsert: tạo record mới nếu chưa có, cập nhật nếu đã tồn tại.

    Args:
        body: Toạ độ GPS mới (latitude, longitude, heading, speed_kmh).
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        DriverLocationResponse với vị trí mới nhất.
    """
    provider = await _get_provider_or_400(current_user, db)

    stmt = select(DriverLocation).where(DriverLocation.provider_id == provider.id)
    location_row = (await db.execute(stmt)).scalars().first()

    if not location_row:
        location_row = DriverLocation(
            provider_id=provider.id,
            latitude=body.latitude,
            longitude=body.longitude,
            heading=body.heading,
            speed_kmh=body.speed_kmh,
        )
        db.add(location_row)
    else:
        location_row.latitude = body.latitude
        location_row.longitude = body.longitude
        location_row.heading = body.heading
        location_row.speed_kmh = body.speed_kmh
        location_row.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(location_row)
    return location_row
