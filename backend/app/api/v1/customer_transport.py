"""Customer API — Tìm kiếm & tra cứu dịch vụ Vận tải & Logistics (Phase 6).

Endpoints:
  GET /customer/transport/search                            Tìm provider vận tải
  GET /customer/transport/routes                           Tìm tuyến xe khách
  GET /customer/transport/routes/{id}                      Chi tiết tuyến + lịch
  GET /customer/transport/rental-vehicles                  Tìm xe cho thuê tự lái
  GET /customer/transport/rental-vehicles/{id}             Chi tiết xe cho thuê
  GET /customer/transport/rental-vehicles/{id}/availabilities  Kiểm tra lịch trống
"""

import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.taxonomy import ServiceCategory
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleAvailability,
    ServiceRoute,
    ServiceRouteSchedule,
)
from app.schemas.transport import (
    AvailabilityItem,
    CustomerRentalVehicleItem,
    CustomerRouteDetailResponse,
    CustomerRouteScheduleItem,
    CustomerRouteSearchItem,
    CustomerTransportSearchItem,
    VehicleAvailabilityResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customer/transport", tags=["customer-transport"])

# Transport-related service category codes
_RENTAL_CAR_CODE = "cho_thue_xe_tu_lai_oto"
_RENTAL_MOTO_CODE = "cho_thue_xe_may"
_BUS_INTERCITY_CODE = "xe_khach_lien_tinh"
_SHARED_RIDE_CODE = "xe_ghep_tien_chuyen"
_LIMOUSINE_CODE = "xe_limousine"


@router.get("/search", response_model=list[CustomerTransportSearchItem])
async def search_transport_providers(
    service_category_code: str = Query(
        ..., description="Mã loại dịch vụ vận tải (taxi_cong_nghe, shipper_noi_thanh, ...)"
    ),
    province: str | None = Query(
        default=None, description="Lọc theo tỉnh/TP phục vụ (tìm trong attributes)"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerTransportSearchItem]:
    """Tìm kiếm provider theo loại dịch vụ vận tải và tỉnh/TP.

    Args:
        service_category_code: Mã loại dịch vụ (từ taxonomy Phase 6).
        province: Tỉnh/TP muốn tìm provider phục vụ.
        limit: Số kết quả tối đa.
        offset: Pagination offset.
        db: Async DB session.

    Returns:
        Danh sách CustomerTransportSearchItem.

    Raises:
        HTTPException 400: Nếu service_category_code không tồn tại.
    """
    # Validate service category
    cat_stmt = select(ServiceCategory).where(
        and_(
            ServiceCategory.code == service_category_code,
            ServiceCategory.is_active == True,  # noqa: E712
        )
    )
    category = (await db.execute(cat_stmt)).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service category '{service_category_code}' not found or inactive",
        )

    # Join provider_services with providers and service_categories
    stmt = (
        select(
            ProviderService.id.label("service_id"),
            ProviderService.provider_id,
            ServiceCategory.code.label("service_category_code"),
            ServiceCategory.name.label("service_category_name"),
            Provider.verification_status,
            Provider.avg_rating,
            Provider.total_reviews,
        )
        .join(Provider, ProviderService.provider_id == Provider.id)
        .join(ServiceCategory, ProviderService.service_category_id == ServiceCategory.id)
        .where(
            and_(
                ProviderService.service_category_id == category.id,
                ProviderService.is_active == True,  # noqa: E712
                Provider.status == "active",
            )
        )
        .order_by(Provider.avg_rating.desc(), Provider.total_reviews.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    results = []
    for row in rows:
        # Build provider display name from available profile
        provider = await db.get(Provider, row.provider_id)
        if provider is None:
            continue

        # Try to get a display name
        from app.models.provider import ProviderIndividualProfile, ProviderBusinessProfile
        biz = await db.get(ProviderBusinessProfile, provider.id)
        ind = await db.get(ProviderIndividualProfile, provider.id)
        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(provider.id)
        )

        results.append(
            CustomerTransportSearchItem(
                provider_id=row.provider_id,
                service_id=row.service_id,
                service_category_code=row.service_category_code,
                service_category_name=row.service_category_name,
                provider_name=provider_name,
                verification_status=row.verification_status,
                avg_rating=float(row.avg_rating),
                total_reviews=row.total_reviews,
            )
        )
    return results


@router.get("/routes", response_model=list[CustomerRouteSearchItem])
async def search_bus_routes(
    from_province: str = Query(..., description="Tỉnh/TP khởi hành"),
    to_province: str = Query(..., description="Tỉnh/TP đến"),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerRouteSearchItem]:
    """Tìm tuyến xe khách liên tỉnh theo điểm đi và đến.

    Args:
        from_province: Tỉnh/TP xuất phát.
        to_province: Tỉnh/TP đến.
        db: Async DB session.

    Returns:
        Danh sách CustomerRouteSearchItem sắp xếp theo giá.
    """
    # Count active schedules per route using subquery
    schedule_count_subq = (
        select(
            ServiceRouteSchedule.route_id,
            func.count(ServiceRouteSchedule.id).label("schedule_count"),
        )
        .where(ServiceRouteSchedule.is_active == True)  # noqa: E712
        .group_by(ServiceRouteSchedule.route_id)
        .subquery()
    )

    stmt = (
        select(
            ServiceRoute.id,
            ServiceRoute.provider_service_id,
            ServiceRoute.from_province,
            ServiceRoute.to_province,
            ServiceRoute.price,
            ServiceRoute.duration_min,
            func.coalesce(schedule_count_subq.c.schedule_count, 0).label("active_schedule_count"),
        )
        .outerjoin(schedule_count_subq, ServiceRoute.id == schedule_count_subq.c.route_id)
        .where(
            and_(
                ServiceRoute.from_province.ilike(f"%{from_province}%"),
                ServiceRoute.to_province.ilike(f"%{to_province}%"),
                ServiceRoute.is_active == True,  # noqa: E712
            )
        )
        .order_by(ServiceRoute.price.asc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        CustomerRouteSearchItem(
            id=row.id,
            provider_service_id=row.provider_service_id,
            from_province=row.from_province,
            to_province=row.to_province,
            price=float(row.price),
            duration_min=row.duration_min,
            active_schedule_count=row.active_schedule_count,
        )
        for row in rows
    ]


@router.get("/routes/{route_id}", response_model=CustomerRouteDetailResponse)
async def get_route_with_schedules(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CustomerRouteDetailResponse:
    """Chi tiết tuyến đường kèm tất cả lịch khởi hành đang hoạt động.

    Args:
        route_id: UUID của tuyến.
        db: Async DB session.

    Returns:
        CustomerRouteDetailResponse chứa route info và danh sách schedules đang active.

    Raises:
        HTTPException 404: Nếu tuyến không tồn tại hoặc đã tắt.
    """
    route_stmt = select(ServiceRoute).where(
        and_(
            ServiceRoute.id == route_id,
            ServiceRoute.is_active == True,  # noqa: E712
        )
    )
    route = (await db.execute(route_stmt)).scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    # Query active schedules explicitly to avoid session identity-map cache issues
    sched_stmt = (
        select(ServiceRouteSchedule)
        .where(
            and_(
                ServiceRouteSchedule.route_id == route_id,
                ServiceRouteSchedule.is_active == True,  # noqa: E712
            )
        )
        .order_by(ServiceRouteSchedule.departure_time)
    )
    active_schedules = (await db.execute(sched_stmt)).scalars().all()

    return CustomerRouteDetailResponse(
        id=route.id,
        provider_service_id=route.provider_service_id,
        from_province=route.from_province,
        to_province=route.to_province,
        distance_km=float(route.distance_km) if route.distance_km else None,
        duration_min=route.duration_min,
        price=float(route.price),
        notes=route.notes,
        schedules=[
            CustomerRouteScheduleItem(
                id=s.id,
                departure_time=str(s.departure_time),
                seat_count=s.seat_count,
            )
            for s in active_schedules
        ],
    )


@router.get("/rental-vehicles", response_model=list[CustomerRentalVehicleItem])
async def search_rental_vehicles(
    vehicle_type: str | None = Query(
        default=None, description="Lọc theo loại xe (xe_4_cho, xe_7_cho, ...)"
    ),
    fuel_type: str | None = Query(default=None, description="Lọc theo nhiên liệu"),
    transmission: str | None = Query(default=None, description="Lọc hộp số: auto/manual"),
    min_seats: int | None = Query(default=None, ge=1, description="Số chỗ tối thiểu"),
    available_on: date | None = Query(
        default=None, description="Ngày muốn thuê (YYYY-MM-DD) — lọc xe còn trống"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerRentalVehicleItem]:
    """Tìm xe ô tô hoặc xe máy cho thuê tự lái.

    Args:
        vehicle_type: Lọc loại xe.
        fuel_type: Lọc nhiên liệu.
        transmission: Lọc hộp số.
        min_seats: Số chỗ tối thiểu.
        available_on: Ngày cần thuê — loại bỏ xe đã bị block.
        limit: Số kết quả tối đa.
        offset: Pagination offset.
        db: Async DB session.

    Returns:
        Danh sách CustomerRentalVehicleItem.
    """
    conditions = [ProviderVehicle.status == "active"]

    if vehicle_type is not None:
        conditions.append(ProviderVehicle.vehicle_type == vehicle_type)
    if fuel_type is not None:
        conditions.append(ProviderVehicle.fuel_type == fuel_type)
    if transmission is not None:
        conditions.append(ProviderVehicle.transmission == transmission)
    if min_seats is not None:
        conditions.append(ProviderVehicle.seat_count >= min_seats)

    # Exclude vehicles blocked on the requested date
    if available_on is not None:
        blocked_subq = (
            select(ProviderVehicleAvailability.vehicle_id)
            .where(
                and_(
                    ProviderVehicleAvailability.date == available_on,
                    ProviderVehicleAvailability.is_blocked == True,  # noqa: E712
                )
            )
            .scalar_subquery()
        )
        conditions.append(ProviderVehicle.id.not_in(blocked_subq))

    stmt = (
        select(ProviderVehicle)
        .where(*conditions)
        .order_by(ProviderVehicle.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    vehicles = (await db.execute(stmt)).scalars().all()
    return [CustomerRentalVehicleItem.model_validate(v) for v in vehicles]


@router.get("/rental-vehicles/{vehicle_id}", response_model=CustomerRentalVehicleItem)
async def get_rental_vehicle_detail(
    vehicle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CustomerRentalVehicleItem:
    """Chi tiết xe cho thuê tự lái.

    Args:
        vehicle_id: UUID của xe.
        db: Async DB session.

    Returns:
        CustomerRentalVehicleItem.

    Raises:
        HTTPException 404: Nếu xe không tìm thấy hoặc không active.
    """
    vehicle = await db.get(ProviderVehicle, vehicle_id)
    if not vehicle or vehicle.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rental vehicle not found",
        )
    return CustomerRentalVehicleItem.model_validate(vehicle)


@router.get(
    "/rental-vehicles/{vehicle_id}/availabilities",
    response_model=VehicleAvailabilityResponse,
)
async def get_rental_vehicle_availabilities(
    vehicle_id: uuid.UUID,
    from_date: date = Query(..., description="Ngày bắt đầu kiểm tra (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Ngày kết thúc kiểm tra (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> VehicleAvailabilityResponse:
    """Kiểm tra lịch trống của xe cho thuê trong khoảng thời gian.

    Trả về các ngày bị block; ngày không có trong kết quả = xe rảnh.

    Args:
        vehicle_id: UUID của xe.
        from_date: Ngày bắt đầu.
        to_date: Ngày kết thúc.
        db: Async DB session.

    Returns:
        VehicleAvailabilityResponse chứa các ngày bị block.

    Raises:
        HTTPException 400: Nếu from_date > to_date.
        HTTPException 404: Nếu xe không tìm thấy.
    """
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before or equal to to_date",
        )

    vehicle = await db.get(ProviderVehicle, vehicle_id)
    if not vehicle or vehicle.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rental vehicle not found",
        )

    stmt = (
        select(ProviderVehicleAvailability)
        .where(
            and_(
                ProviderVehicleAvailability.vehicle_id == vehicle_id,
                ProviderVehicleAvailability.date >= from_date,
                ProviderVehicleAvailability.date <= to_date,
                ProviderVehicleAvailability.is_blocked == True,  # noqa: E712
            )
        )
        .order_by(ProviderVehicleAvailability.date)
    )
    items = (await db.execute(stmt)).scalars().all()

    return VehicleAvailabilityResponse(
        vehicle_id=vehicle_id,
        items=[AvailabilityItem.model_validate(i) for i in items],
    )
