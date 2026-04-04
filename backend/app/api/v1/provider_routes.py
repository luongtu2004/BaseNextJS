"""Provider API — Quản lý tuyến đường & lịch khởi hành (Phase 6.3).

Endpoints:
  POST   /provider/services/{svc_id}/routes
  GET    /provider/services/{svc_id}/routes
  GET    /provider/services/{svc_id}/routes/{route_id}
  PUT    /provider/services/{svc_id}/routes/{route_id}
  PATCH  /provider/services/{svc_id}/routes/{route_id}/status
  DELETE /provider/services/{svc_id}/routes/{route_id}

  POST   /provider/routes/{route_id}/schedules
  GET    /provider/routes/{route_id}/schedules
  PUT    /provider/routes/{route_id}/schedules/{schedule_id}
  PATCH  /provider/routes/{route_id}/schedules/{schedule_id}/status
  DELETE /provider/routes/{route_id}/schedules/{schedule_id}
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.transport import ServiceRoute, ServiceRouteSchedule
from app.models.user import User
from app.schemas.transport import (
    RouteStatusPatch,
    ScheduleStatusPatch,
    ServiceRouteCreate,
    ServiceRouteResponse,
    ServiceRouteScheduleCreate,
    ServiceRouteScheduleResponse,
    ServiceRouteScheduleUpdate,
    ServiceRouteUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/provider", tags=["provider-routes"])


# ─────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────


async def _get_provider_or_403(current_user: User, db: AsyncSession) -> Provider:
    """Lấy provider của user hoặc raise 403.

    Args:
        current_user: Authenticated user.
        db: Async DB session.

    Returns:
        Provider record.

    Raises:
        HTTPException 403: Nếu user không có provider profile.
    """
    stmt = select(Provider).where(Provider.owner_user_id == current_user.id)
    provider = (await db.execute(stmt)).scalar_one_or_none()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a service provider",
        )
    return provider


async def _get_service_or_404(
    svc_id: uuid.UUID,
    provider_id: uuid.UUID,
    db: AsyncSession,
) -> ProviderService:
    """Lấy provider service và validate ownership.

    Args:
        svc_id: UUID của service.
        provider_id: UUID của provider sở hữu.
        db: Async DB session.

    Returns:
        ProviderService record.

    Raises:
        HTTPException 404: Nếu service không tìm thấy hoặc không thuộc provider.
    """
    stmt = select(ProviderService).where(
        and_(
            ProviderService.id == svc_id,
            ProviderService.provider_id == provider_id,
        )
    )
    svc = (await db.execute(stmt)).scalar_one_or_none()
    if not svc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider service not found",
        )
    return svc


async def _get_route_or_404(
    route_id: uuid.UUID,
    provider_service_id: uuid.UUID,
    db: AsyncSession,
) -> ServiceRoute:
    """Lấy tuyến đường và validate thuộc đúng service.

    Args:
        route_id: UUID của tuyến.
        provider_service_id: UUID của service chứa tuyến.
        db: Async DB session.

    Returns:
        ServiceRoute với schedules đã load.

    Raises:
        HTTPException 404: Nếu tuyến không tìm thấy.
    """
    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(
            and_(
                ServiceRoute.id == route_id,
                ServiceRoute.provider_service_id == provider_service_id,
            )
        )
    )
    route = (await db.execute(stmt)).scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    return route


async def _get_route_by_id_for_provider(
    route_id: uuid.UUID,
    provider_id: uuid.UUID,
    db: AsyncSession,
) -> ServiceRoute:
    """Lấy tuyến và xác minh thuộc provider qua JOIN với provider_services.

    Args:
        route_id: UUID của tuyến.
        provider_id: UUID của provider.
        db: Async DB session.

    Returns:
        ServiceRoute.

    Raises:
        HTTPException 404: Nếu tuyến không tìm thấy.
    """
    stmt = (
        select(ServiceRoute)
        .join(ProviderService, ServiceRoute.provider_service_id == ProviderService.id)
        .options(selectinload(ServiceRoute.schedules))
        .where(
            and_(
                ServiceRoute.id == route_id,
                ProviderService.provider_id == provider_id,
            )
        )
    )
    route = (await db.execute(stmt)).scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    return route


async def _get_schedule_or_404(
    schedule_id: uuid.UUID,
    route_id: uuid.UUID,
    db: AsyncSession,
) -> ServiceRouteSchedule:
    """Lấy lịch khởi hành theo ID và validate thuộc đúng tuyến.

    Args:
        schedule_id: UUID của lịch.
        route_id: UUID của tuyến.
        db: Async DB session.

    Returns:
        ServiceRouteSchedule.

    Raises:
        HTTPException 404: Nếu lịch không tìm thấy.
    """
    stmt = select(ServiceRouteSchedule).where(
        and_(
            ServiceRouteSchedule.id == schedule_id,
            ServiceRouteSchedule.route_id == route_id,
        )
    )
    schedule = (await db.execute(stmt)).scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )
    return schedule


# ─────────────────────────────────────────────────────────────────────
# Routes CRUD
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/services/{svc_id}/routes",
    response_model=ServiceRouteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_route(
    svc_id: uuid.UUID,
    body: ServiceRouteCreate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Tạo tuyến đường mới cho một dịch vụ xe khách/liên tỉnh.

    Args:
        svc_id: UUID của provider service.
        body: Thông tin tuyến.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse của tuyến vừa tạo.

    Raises:
        HTTPException 400: Nếu from_province == to_province hoặc price <= 0.
        HTTPException 404: Nếu service không thuộc provider.
    """
    if body.from_province.strip().lower() == body.to_province.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_province and to_province must be different",
        )

    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)

    logger.info(
        "[ROUTE] Creating route - svc_id=%s from=%s to=%s",
        svc_id, body.from_province, body.to_province,
    )

    route = ServiceRoute(
        provider_service_id=svc_id,
        from_province=body.from_province,
        to_province=body.to_province,
        distance_km=body.distance_km,
        duration_min=body.duration_min,
        price=body.price,
        notes=body.notes,
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)

    logger.info("[ROUTE] Route created - route_id=%s", route.id)
    # Re-fetch with schedules relationship loaded
    return ServiceRouteResponse.model_validate(
        await _get_route_or_404(route.id, svc_id, db)
    )


@router.get("/services/{svc_id}/routes", response_model=dict)
async def list_routes(
    svc_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Kích thước trang"),
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Danh sách tuyến của một dịch vụ.

    Args:
        svc_id: UUID của provider service.
        page: Số trang hiện tại.
        page_size: Số mục trên mỗi trang.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách các tuyến ở dạng phân trang.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)

    from sqlalchemy import func
    count_stmt = select(func.count(ServiceRoute.id)).where(ServiceRoute.provider_service_id == svc_id)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(ServiceRoute.provider_service_id == svc_id)
        .order_by(ServiceRoute.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    routes = (await db.execute(stmt)).scalars().all()
    items = [ServiceRouteResponse.model_validate(r) for r in routes]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/services/{svc_id}/routes/{route_id}", response_model=ServiceRouteResponse)
async def get_route(
    svc_id: uuid.UUID,
    route_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Chi tiết một tuyến đường kèm tất cả lịch khởi hành.

    Args:
        svc_id: UUID của provider service.
        route_id: UUID của tuyến.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse kèm schedules.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)
    route = await _get_route_or_404(route_id, svc_id, db)
    return ServiceRouteResponse.model_validate(route)


@router.put("/services/{svc_id}/routes/{route_id}", response_model=ServiceRouteResponse)
async def update_route(
    svc_id: uuid.UUID,
    route_id: uuid.UUID,
    body: ServiceRouteUpdate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Cập nhật thông tin tuyến đường.

    Args:
        svc_id: UUID của provider service.
        route_id: UUID của tuyến.
        body: Thông tin cần cập nhật.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse sau khi cập nhật.

    Raises:
        HTTPException 400: Nếu from/to province giống nhau sau update.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)
    route = await _get_route_or_404(route_id, svc_id, db)

    update_data = body.model_dump(exclude_unset=True)

    # Validate province constraint after applying update
    final_from = update_data.get("from_province", route.from_province)
    final_to = update_data.get("to_province", route.to_province)
    if final_from.strip().lower() == final_to.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_province and to_province must be different",
        )

    for field, value in update_data.items():
        setattr(route, field, value)

    route.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(route)
    return ServiceRouteResponse.model_validate(
        await _get_route_or_404(route.id, svc_id, db)
    )


@router.patch("/services/{svc_id}/routes/{route_id}/status", response_model=ServiceRouteResponse)
async def patch_route_status(
    svc_id: uuid.UUID,
    route_id: uuid.UUID,
    body: RouteStatusPatch,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Bật / tắt tuyến đường.

    Args:
        svc_id: UUID của provider service.
        route_id: UUID của tuyến.
        body: is_active mới.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse sau khi thay đổi.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)
    route = await _get_route_or_404(route_id, svc_id, db)

    route.is_active = body.is_active
    route.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(route)
    return ServiceRouteResponse.model_validate(
        await _get_route_or_404(route.id, svc_id, db)
    )


@router.delete(
    "/services/{svc_id}/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_route(
    svc_id: uuid.UUID,
    route_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Xóa tuyến đường. Tất cả lịch sẽ bị xóa theo (cascade).

    Args:
        svc_id: UUID của provider service.
        route_id: UUID của tuyến.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Raises:
        HTTPException 404: Nếu tuyến không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_service_or_404(svc_id, provider.id, db)
    route = await _get_route_or_404(route_id, svc_id, db)
    await db.delete(route)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────
# Schedules CRUD
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/routes/{route_id}/schedules",
    response_model=ServiceRouteScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    route_id: uuid.UUID,
    body: ServiceRouteScheduleCreate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteScheduleResponse:
    """Thêm lịch khởi hành vào tuyến.

    Args:
        route_id: UUID của tuyến.
        body: Thông tin lịch.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteScheduleResponse vừa tạo.

    Raises:
        HTTPException 409: Nếu giờ khởi hành đã tồn tại trên tuyến này.
    """
    provider = await _get_provider_or_403(current_user, db)
    route = await _get_route_by_id_for_provider(route_id, provider.id, db)

    # Check duplicate departure time
    dup_stmt = select(ServiceRouteSchedule).where(
        and_(
            ServiceRouteSchedule.route_id == route_id,
            ServiceRouteSchedule.departure_time == body.departure_time,
        )
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A schedule at {body.departure_time} already exists for this route",
        )

    schedule = ServiceRouteSchedule(
        route_id=route.id,
        departure_time=body.departure_time,
        seat_count=body.seat_count,
        notes=body.notes,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return ServiceRouteScheduleResponse.model_validate(schedule)


@router.get(
    "/routes/{route_id}/schedules",
    response_model=dict,
)
async def list_schedules(
    route_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Kích thước trang"),
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Danh sách lịch khởi hành của một tuyến.

    Args:
        route_id: UUID của tuyến.
        page: Số trang hiện tại.
        page_size: Kích thước trang.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách ServiceRouteScheduleResponse phân trang và sắp xếp theo giờ.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_route_by_id_for_provider(route_id, provider.id, db)

    from sqlalchemy import func
    count_stmt = select(func.count(ServiceRouteSchedule.id)).where(ServiceRouteSchedule.route_id == route_id)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ServiceRouteSchedule)
        .where(ServiceRouteSchedule.route_id == route_id)
        .order_by(ServiceRouteSchedule.departure_time)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    schedules = (await db.execute(stmt)).scalars().all()
    items = [ServiceRouteScheduleResponse.model_validate(s) for s in schedules]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.put(
    "/routes/{route_id}/schedules/{schedule_id}",
    response_model=ServiceRouteScheduleResponse,
)
async def update_schedule(
    route_id: uuid.UUID,
    schedule_id: uuid.UUID,
    body: ServiceRouteScheduleUpdate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteScheduleResponse:
    """Cập nhật lịch khởi hành.

    Args:
        route_id: UUID của tuyến.
        schedule_id: UUID của lịch.
        body: Thông tin cần cập nhật.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteScheduleResponse sau khi cập nhật.

    Raises:
        HTTPException 409: Nếu giờ mới đã tồn tại trên tuyến.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_route_by_id_for_provider(route_id, provider.id, db)
    schedule = await _get_schedule_or_404(schedule_id, route_id, db)

    # Check duplicate time if changing departure_time
    if body.departure_time is not None and body.departure_time != schedule.departure_time:
        dup_stmt = select(ServiceRouteSchedule).where(
            and_(
                ServiceRouteSchedule.route_id == route_id,
                ServiceRouteSchedule.departure_time == body.departure_time,
                ServiceRouteSchedule.id != schedule_id,
            )
        )
        if (await db.execute(dup_stmt)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A schedule at {body.departure_time} already exists for this route",
            )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    schedule.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(schedule)
    return ServiceRouteScheduleResponse.model_validate(schedule)


@router.patch(
    "/routes/{route_id}/schedules/{schedule_id}/status",
    response_model=ServiceRouteScheduleResponse,
)
async def patch_schedule_status(
    route_id: uuid.UUID,
    schedule_id: uuid.UUID,
    body: ScheduleStatusPatch,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteScheduleResponse:
    """Bật / tắt một lịch khởi hành cụ thể.

    Args:
        route_id: UUID của tuyến.
        schedule_id: UUID của lịch.
        body: is_active mới.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteScheduleResponse sau khi thay đổi.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_route_by_id_for_provider(route_id, provider.id, db)
    schedule = await _get_schedule_or_404(schedule_id, route_id, db)

    schedule.is_active = body.is_active
    schedule.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(schedule)
    return ServiceRouteScheduleResponse.model_validate(schedule)


@router.delete(
    "/routes/{route_id}/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_schedule(
    route_id: uuid.UUID,
    schedule_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Xóa một lịch khởi hành.

    Args:
        route_id: UUID của tuyến.
        schedule_id: UUID của lịch.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Raises:
        HTTPException 404: Nếu lịch không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_route_by_id_for_provider(route_id, provider.id, db)
    schedule = await _get_schedule_or_404(schedule_id, route_id, db)
    await db.delete(schedule)
    await db.commit()
