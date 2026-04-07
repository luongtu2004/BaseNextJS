from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
    radius_km: float = Query(default=10.0, ge=1.0, le=50.0, description="Bán kính tìm kiếm (km)"),
    page: int = Query(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_provider_user),
) -> dict:
    """Danh sách các cuốc xe đang chờ nhận.

    Tài xế dùng API này để duyệt các booking `pending`. MVP lấy các cuốc chờ có
    điểm đón (`pickup_point`) nằm trong bán kính `radius_km` so với vị trí hiện tại
    của tài xế, sử dụng PostGIS spatial query mạnh mẽ.

    Args:
        service_type: Lọc theo loại dịch vụ.
        radius_km: Bán kính tìm kiếm tính từ vị trí tài xế (mặc định 5km, tối đa 50km).
        page: Số trang hiện tại.
        page_size: Số mục trên mỗi trang.
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        Dict phân trang chứa danh sách items (BookingSummaryResponse — không có OTP),
        page, page_size, total.
    """
    provider = await _get_provider_or_400(current_user, db)
    logger.info("[BOOKING] Provider %s browsing available bookings within %skm", current_user.id, radius_km)

    # Get driver's current location
    driver_loc = await db.get(DriverLocation, provider.id)

    # Query setup
    conditions = [Booking.status == "pending"]
    if service_type:
        conditions.append(Booking.service_type == service_type)

    if driver_loc and driver_loc.location is not None:
        radius_meters = radius_km * 1000
        # Spatial filter using PostGIS ST_DWithin (utilizes GIST index)
        # Note: ST_DWithin requires Geography parameters for meters
        conditions.append(
            func.ST_DWithin(
                Booking.pickup_point,
                driver_loc.location,
                radius_meters
            )
        )
        
        # Calculate distance for sorting and front-end display
        dist_expr = func.ST_Distance(Booking.pickup_point, driver_loc.location)
        select_cols = [Booking, dist_expr.label("distance_meters")]
        base_query = select(*select_cols).where(*conditions)
        
        count_stmt = select(func.count()).where(*conditions)
        query = (
            base_query
            .order_by(dist_expr.asc())  # Nearest first
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    else:
        # Fallback if driver has no known location
        from sqlalchemy import literal
        base_query = select(Booking, literal(0.0).label("distance_meters")).where(*conditions)
        count_stmt = select(func.count()).where(*conditions)
        query = (
            base_query
            .order_by(Booking.requested_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(query)
    
    items = []
    for row in result:
        b = row[0]
        # Calculate distance in km
        dist_km = (float(row[1]) / 1000.0) if row[1] is not None else None
        
        b_dict = BookingSummaryResponse.model_validate(b).model_dump()
        b_dict["distance_km"] = dist_km
        items.append(b_dict)

    return {
        "items": items,
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
    now_utc = datetime.now(tz=timezone.utc)

    # Performance: single UPDATE + RETURNING, fall back to INSERT only if no row exists
    update_stmt = (
        sa_update(DriverAvailabilitySession)
        .where(DriverAvailabilitySession.provider_id == provider.id)
        .values(
            vehicle_id=body.vehicle_id,
            status="online",
            online_at=now_utc,
            offline_at=None,
        )
        .returning(DriverAvailabilitySession)
    )
    result = (await db.execute(update_stmt)).scalars().first()
    if not result:
        # First time going online — create session
        new_session = DriverAvailabilitySession(
            provider_id=provider.id,
            vehicle_id=body.vehicle_id,
            status="online",
            online_at=now_utc,
        )
        db.add(new_session)
        await db.flush()
        result = new_session

    await db.commit()
    await db.refresh(result)
    return DriverAvailabilitySessionResponse.model_validate(result)


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
    now_utc = datetime.now(tz=timezone.utc)

    # Performance: single UPDATE + RETURNING (no SELECT needed)
    update_stmt = (
        sa_update(DriverAvailabilitySession)
        .where(DriverAvailabilitySession.provider_id == provider.id)
        .values(status="offline", offline_at=now_utc)
        .returning(DriverAvailabilitySession)
    )
    result = (await db.execute(update_stmt)).scalars().first()
    if not result:
        raise HTTPException(status_code=400, detail="No active session found")

    await db.commit()
    await db.refresh(result)
    return DriverAvailabilitySessionResponse.model_validate(result)


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

    # Performance: PostgreSQL INSERT ON CONFLICT UPDATE -- single round-trip
    # driver_locations has provider_id as PRIMARY KEY so conflict on PK
    stmt = (
        pg_insert(DriverLocation)
        .values(
            provider_id=provider.id,
            latitude=body.latitude,
            longitude=body.longitude,
            heading=body.heading,
            speed_kmh=body.speed_kmh,
            location=func.ST_SetSRID(func.ST_MakePoint(body.longitude, body.latitude), 4326),
            updated_at=func.now(),
        )
        .on_conflict_do_update(
            index_elements=["provider_id"],  # string column name (PK)
            set_={
                "latitude": body.latitude,
                "longitude": body.longitude,
                "heading": body.heading,
                "speed_kmh": body.speed_kmh,
                "location": func.ST_SetSRID(func.ST_MakePoint(body.longitude, body.latitude), 4326),
                "updated_at": func.now(),
            },
        )
        .returning(DriverLocation)
    )
    location_row = (await db.execute(stmt)).scalars().one()
    await db.commit()
    return DriverLocationResponse.model_validate(location_row)
