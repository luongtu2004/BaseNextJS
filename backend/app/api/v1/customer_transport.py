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

from app.db.session import get_db
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile
from app.models.provider_service import ProviderService, ProviderServiceAttribute
from app.models.taxonomy import ServiceCategory
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleAvailability,
    ServiceRoute,
    ServiceRouteSchedule,
)
from app.models.user import User

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
    service_category_code: str | None = Query(
        default=None, description="Mã loại dịch vụ vận tải — bỏ trống để tìm tất cả provider transport"
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
    conditions = [
        ProviderService.is_active == True,  # noqa: E712
        Provider.status == "active",
    ]

    # Validate & filter by service category when provided
    if service_category_code is not None:
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
        conditions.append(ProviderService.service_category_id == category.id)

    # Fix: Apply province filter via ProviderServiceAttribute EXISTS subquery
    if province:
        province_exists = (
            select(ProviderServiceAttribute.id)
            .where(
                and_(
                    ProviderServiceAttribute.provider_service_id == ProviderService.id,
                    ProviderServiceAttribute.value_text.ilike(f"%{province}%"),
                )
            )
            .exists()
        )
        conditions.append(province_exists)

    stmt = (
        select(
            ProviderService.id.label("service_id"),
            ProviderService.provider_id,
            ProviderService.base_price,
            ProviderService.price_unit,
            ProviderService.description.label("service_description"),
            ServiceCategory.code.label("service_category_code"),
            ServiceCategory.name.label("service_category_name"),
            Provider.provider_type,
            Provider.description.label("provider_description"),
            Provider.verification_status,
            Provider.avg_rating,
            Provider.total_reviews,
            Provider.total_jobs_completed,
            Provider.owner_user_id,
        )
        .join(Provider, ProviderService.provider_id == Provider.id)
        .join(ServiceCategory, ProviderService.service_category_id == ServiceCategory.id)
        .where(*conditions)
        .order_by(Provider.avg_rating.desc(), Provider.total_reviews.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    if not rows:
        return []

    # Bulk load profiles (avoid N+1)
    provider_ids = list({row.provider_id for row in rows})
    owner_ids = list({row.owner_user_id for row in rows if row.owner_user_id})

    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    from app.models.user import User as _User
    user_map: dict = {
        u.id: u
        for u in (await db.execute(
            select(_User).where(_User.id.in_(owner_ids))
        )).scalars().all()
    } if owner_ids else {}

    results = []
    for row in rows:
        biz = biz_map.get(row.provider_id)
        ind = ind_map.get(row.provider_id)
        user = user_map.get(row.owner_user_id)

        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(row.provider_id)
        )

        results.append(
            CustomerTransportSearchItem(
                provider_id=row.provider_id,
                service_id=row.service_id,
                service_category_code=row.service_category_code,
                service_category_name=row.service_category_name,
                provider_name=provider_name,
                provider_type=row.provider_type,
                description=row.provider_description,
                phone=user.phone if user else None,
                hotline=biz.hotline if biz else None,
                avatar_url=user.avatar_url if user else None,
                avg_rating=float(row.avg_rating),
                total_reviews=row.total_reviews,
                total_jobs_completed=row.total_jobs_completed,
                verification_status=row.verification_status,
                service_description=row.service_description,
                base_price=float(row.base_price) if row.base_price else None,
                price_unit=row.price_unit,
            )
        )
    return results


@router.get("/routes", response_model=list[CustomerRouteSearchItem])
async def search_bus_routes(
    from_province: str | None = Query(default=None, description="Tỉnh/TP khởi hành — bỏ trống để hiển thị tất cả"),
    to_province: str | None = Query(default=None, description="Tỉnh/TP đến — bỏ trống để hiển thị tất cả"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerRouteSearchItem]:
    """Tìm tuyến xe khách liên tỉnh theo điểm đi và đến.

    Args:
        from_province: Tỉnh/TP xuất phát (bỏ trống = tất cả).
        to_province: Tỉnh/TP đến (bỏ trống = tất cả).
        limit: Số kết quả tối đa.
        offset: Pagination offset.
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

    route_conditions: list = [ServiceRoute.is_active == True]  # noqa: E712
    if from_province:
        route_conditions.append(ServiceRoute.from_province.ilike(f"%{from_province}%"))
    if to_province:
        route_conditions.append(ServiceRoute.to_province.ilike(f"%{to_province}%"))

    stmt = (
        select(
            ServiceRoute.id,
            ServiceRoute.provider_service_id,
            ServiceRoute.from_province,
            ServiceRoute.to_province,
            ServiceRoute.price,
            ServiceRoute.distance_km,
            ServiceRoute.duration_min,
            ServiceRoute.notes,
            func.coalesce(schedule_count_subq.c.schedule_count, 0).label("active_schedule_count"),
            ProviderService.provider_id,
            Provider.avg_rating,
            Provider.total_reviews,
            Provider.verification_status,
            Provider.owner_user_id,
        )
        .outerjoin(schedule_count_subq, ServiceRoute.id == schedule_count_subq.c.route_id)
        .join(ProviderService, ServiceRoute.provider_service_id == ProviderService.id)
        .join(Provider, ProviderService.provider_id == Provider.id)
        .where(*route_conditions)
        .order_by(ServiceRoute.price.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    if not rows:
        return []

    # Bulk load provider profiles + user phone
    provider_ids = list({row.provider_id for row in rows})
    owner_ids = list({row.owner_user_id for row in rows if row.owner_user_id})

    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    user_map: dict = {
        u.id: u
        for u in (await db.execute(
            select(User).where(User.id.in_(owner_ids))
        )).scalars().all()
    } if owner_ids else {}

    results = []
    for row in rows:
        biz = biz_map.get(row.provider_id)
        ind = ind_map.get(row.provider_id)
        user = user_map.get(row.owner_user_id)
        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(row.provider_id)
        )
        results.append(
            CustomerRouteSearchItem(
                id=row.id,
                provider_service_id=row.provider_service_id,
                provider_id=row.provider_id,
                provider_name=provider_name,
                phone=user.phone if user else None,
                hotline=biz.hotline if biz else None,
                avg_rating=float(row.avg_rating) if row.avg_rating else None,
                total_reviews=row.total_reviews,
                verification_status=row.verification_status,
                from_province=row.from_province,
                to_province=row.to_province,
                distance_km=float(row.distance_km) if row.distance_km else None,
                price=float(row.price),
                duration_min=row.duration_min,
                active_schedule_count=row.active_schedule_count,
                notes=row.notes,
            )
        )
    return results


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

    # Load provider info from linked ProviderService
    svc_stmt = select(ProviderService).where(ProviderService.id == route.provider_service_id)
    svc = (await db.execute(svc_stmt)).scalar_one_or_none()
    provider_id = svc.provider_id if svc else None

    provider_name = str(provider_id) if provider_id else "N/A"
    hotline = None
    phone = None
    avg_rating = None
    total_reviews = None
    provider_type = None
    verification_status = None
    if provider_id:
        provider = await db.get(Provider, provider_id)
        biz = await db.get(ProviderBusinessProfile, provider_id)
        ind = await db.get(ProviderIndividualProfile, provider_id)
        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(provider_id)
        )
        hotline = biz.hotline if biz else None
        if provider:
            avg_rating = float(provider.avg_rating) if provider.avg_rating else None
            total_reviews = provider.total_reviews
            provider_type = provider.provider_type
            verification_status = provider.verification_status
            user = await db.get(User, provider.owner_user_id)
            phone = user.phone if user else None

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
        provider_id=provider_id,
        provider_name=provider_name,
        phone=phone,
        hotline=hotline,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        provider_type=provider_type,
        verification_status=verification_status,
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
    has_ac: bool | None = Query(default=None, description="Lọc có điều hòa"),
    has_wifi: bool | None = Query(default=None, description="Lọc có WiFi"),
    available_on: date | None = Query(
        default=None, description="Ngày muốn thuê (YYYY-MM-DD) — lọc xe còn trống"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerRentalVehicleItem]:
    """Tìm xe ô tô hoặc xe máy cho thuê tự lái.

    Chỉ trả về xe thuộc service category cho_thue_xe_tu_lai_oto hoặc cho_thue_xe_may.

    Args:
        vehicle_type: Lọc loại xe.
        fuel_type: Lọc nhiên liệu.
        transmission: Lọc hộp số.
        min_seats: Số chỗ tối thiểu.
        has_ac: Lọc có điều hòa.
        has_wifi: Lọc có WiFi.
        available_on: Ngày cần thuê — loại bỏ xe đã bị block.
        limit: Số kết quả tối đa.
        offset: Pagination offset.
        db: Async DB session.

    Returns:
        Danh sách CustomerRentalVehicleItem.
    """
    conditions: list = [ProviderVehicle.status == "active"]

    if vehicle_type is not None:
        conditions.append(ProviderVehicle.vehicle_type == vehicle_type)
    if fuel_type is not None:
        conditions.append(ProviderVehicle.fuel_type == fuel_type)
    if transmission is not None:
        conditions.append(ProviderVehicle.transmission == transmission)
    if min_seats is not None:
        conditions.append(ProviderVehicle.seat_count >= min_seats)
    if has_ac is not None:
        conditions.append(ProviderVehicle.has_ac == has_ac)
    if has_wifi is not None:
        conditions.append(ProviderVehicle.has_wifi == has_wifi)

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

    if not vehicles:
        return []

    # Bulk load provider profiles, service pricing, and provider ratings
    provider_ids = list({v.provider_id for v in vehicles})
    service_ids = list({v.service_id for v in vehicles if v.service_id})

    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(provider_ids))
        )).scalars().all()
    }
    svc_map: dict = (
        {
            s.id: s
            for s in (await db.execute(
                select(ProviderService).where(ProviderService.id.in_(service_ids))
            )).scalars().all()
        }
        if service_ids
        else {}
    )
    prov_map: dict = {
        p.id: p
        for p in (await db.execute(
            select(Provider).where(Provider.id.in_(provider_ids))
        )).scalars().all()
    }
    owner_ids = list({p.owner_user_id for p in prov_map.values() if p.owner_user_id})
    user_map: dict = {
        u.id: u
        for u in (await db.execute(
            select(User).where(User.id.in_(owner_ids))
        )).scalars().all()
    } if owner_ids else {}

    results = []
    for v in vehicles:
        biz = biz_map.get(v.provider_id)
        ind = ind_map.get(v.provider_id)
        svc = svc_map.get(v.service_id) if v.service_id else None
        prov = prov_map.get(v.provider_id)
        user = user_map.get(prov.owner_user_id) if prov and prov.owner_user_id else None
        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(v.provider_id)
        )
        results.append(
            CustomerRentalVehicleItem(
                id=v.id,
                provider_id=v.provider_id,
                provider_name=provider_name,
                phone=user.phone if user else None,
                hotline=biz.hotline if biz else None,
                avg_rating=float(prov.avg_rating) if prov and prov.avg_rating else None,
                total_reviews=prov.total_reviews if prov else None,
                vehicle_type=v.vehicle_type,
                vehicle_brand=v.vehicle_brand,
                vehicle_model=v.vehicle_model,
                year_of_manufacture=v.year_of_manufacture,
                seat_count=v.seat_count,
                fuel_type=v.fuel_type,
                transmission=v.transmission,
                has_ac=v.has_ac,
                has_wifi=v.has_wifi,
                color=v.color,
                notes=v.notes,
                status=v.status,
                base_price=float(svc.base_price) if svc and svc.base_price else None,
                price_unit=svc.price_unit if svc else None,
            )
        )
    return results


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

    prov = await db.get(Provider, vehicle.provider_id)
    biz = await db.get(ProviderBusinessProfile, vehicle.provider_id)
    ind = await db.get(ProviderIndividualProfile, vehicle.provider_id)
    provider_name = (
        (biz.company_name if biz else None)
        or (ind.full_name if ind else None)
        or str(vehicle.provider_id)
    )

    svc = await db.get(ProviderService, vehicle.service_id) if vehicle.service_id else None

    # Load user for phone
    phone = None
    if prov and prov.owner_user_id:
        user = await db.get(User, prov.owner_user_id)
        phone = user.phone if user else None

    return CustomerRentalVehicleItem(
        id=vehicle.id,
        provider_id=vehicle.provider_id,
        provider_name=provider_name,
        phone=phone,
        hotline=biz.hotline if biz else None,
        avg_rating=float(prov.avg_rating) if prov and prov.avg_rating else None,
        total_reviews=prov.total_reviews if prov else None,
        vehicle_type=vehicle.vehicle_type,
        vehicle_brand=vehicle.vehicle_brand,
        vehicle_model=vehicle.vehicle_model,
        year_of_manufacture=vehicle.year_of_manufacture,
        seat_count=vehicle.seat_count,
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
        has_ac=vehicle.has_ac,
        has_wifi=vehicle.has_wifi,
        color=vehicle.color,
        notes=vehicle.notes,
        status=vehicle.status,
        base_price=float(svc.base_price) if svc and svc.base_price else None,
        price_unit=svc.price_unit if svc else None,
    )


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
