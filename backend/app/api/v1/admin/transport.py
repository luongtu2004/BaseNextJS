"""Admin API — Quản lý phương tiện, giấy tờ xe, và tuyến đường (Phase 6).

Endpoints:
  GET    /admin/vehicles              Danh sách tất cả xe
  GET    /admin/vehicles/{id}         Chi tiết xe
  PATCH  /admin/vehicles/{id}/status  Kích hoạt / khoá xe

  GET    /admin/vehicle-documents              Queue giấy tờ chờ duyệt
  POST   /admin/vehicle-documents/{doc_id}/review   Duyệt / từ chối

  GET    /admin/routes                Tất cả tuyến đường
  GET    /admin/routes/{id}           Chi tiết tuyến + lịch
  PATCH  /admin/routes/{id}/status    Bật / tắt tuyến
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleDocument,
    ServiceRoute,
)
from app.models.user import User
from app.schemas.transport import (
    AdminVehicleStatusPatch,
    ProviderVehicleResponse,
    RouteStatusPatch,
    ServiceRouteResponse,
    VehicleDocumentResponse,
    VehicleDocumentReviewRequest,
    VehicleStatusPatch,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-transport"])


# ─────────────────────────────────────────────────────────────────────
# Admin — Vehicles
# ─────────────────────────────────────────────────────────────────────


@router.get("/vehicles", response_model=list[ProviderVehicleResponse])
async def admin_list_vehicles(
    provider_id: uuid.UUID | None = Query(default=None, description="Lọc theo provider"),
    vehicle_type: str | None = Query(default=None, description="Lọc theo loại xe"),
    status_filter: str | None = Query(default=None, alias="status", description="Lọc theo status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderVehicleResponse]:
    """Danh sách tất cả xe trong hệ thống. Hỗ trợ filter và pagination.

    Args:
        provider_id: Lọc theo provider cụ thể.
        vehicle_type: Lọc theo loại xe.
        status_filter: Lọc theo trạng thái (active/inactive/suspended).
        limit: Số bản ghi tối đa.
        offset: Bắt đầu từ vị trí nào.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách ProviderVehicleResponse.
    """
    conditions = []
    if provider_id is not None:
        conditions.append(ProviderVehicle.provider_id == provider_id)
    if vehicle_type is not None:
        conditions.append(ProviderVehicle.vehicle_type == vehicle_type)
    if status_filter is not None:
        conditions.append(ProviderVehicle.status == status_filter)

    stmt = (
        select(ProviderVehicle)
        .where(*conditions)
        .order_by(ProviderVehicle.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    vehicles = (await db.execute(stmt)).scalars().all()
    return [ProviderVehicleResponse.model_validate(v) for v in vehicles]


@router.get("/vehicles/{vehicle_id}", response_model=ProviderVehicleResponse)
async def admin_get_vehicle(
    vehicle_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Chi tiết xe theo ID.

    Args:
        vehicle_id: UUID của xe.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse.

    Raises:
        HTTPException 404: Nếu xe không tìm thấy.
    """
    vehicle = await db.get(ProviderVehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return ProviderVehicleResponse.model_validate(vehicle)


@router.patch("/vehicles/{vehicle_id}/status", response_model=ProviderVehicleResponse)
async def admin_patch_vehicle_status(
    vehicle_id: uuid.UUID,
    body: AdminVehicleStatusPatch,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Admin kích hoạt hoặc khoá xe.

    Args:
        vehicle_id: UUID của xe.
        body: status mới.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse sau khi thay đổi.

    Raises:
        HTTPException 404: Nếu xe không tìm thấy.
    """
    vehicle = await db.get(ProviderVehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    logger.info(
        "[ADMIN] Vehicle status change - vehicle_id=%s old=%s new=%s admin=%s",
        vehicle.id, vehicle.status, body.status, current_admin.id,
    )

    vehicle.status = body.status
    vehicle.updated_at = datetime.now(tz=timezone.utc)
    vehicle.updated_by = current_admin.id
    await db.commit()
    await db.refresh(vehicle)
    return ProviderVehicleResponse.model_validate(vehicle)


# ─────────────────────────────────────────────────────────────────────
# Admin — Vehicle Documents
# ─────────────────────────────────────────────────────────────────────


@router.get("/vehicle-documents", response_model=list[VehicleDocumentResponse])
async def admin_list_vehicle_documents(
    review_status: str | None = Query(
        default="pending", description="Lọc theo trạng thái duyệt: pending/approved/rejected"
    ),
    vehicle_id: uuid.UUID | None = Query(default=None, description="Lọc theo xe cụ thể"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[VehicleDocumentResponse]:
    """Queue giấy tờ xe chờ duyệt dành cho admin CMS.

    Args:
        review_status: Lọc theo trạng thái: pending (default), approved, rejected, hoặc None.
        vehicle_id: Lọc theo xe cụ thể.
        limit: Số bản ghi tối đa.
        offset: Pagination offset.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách VehicleDocumentResponse sắp xếp từ cũ đến mới (FIFO review).
    """
    conditions = []
    if review_status is not None:
        conditions.append(ProviderVehicleDocument.review_status == review_status)
    if vehicle_id is not None:
        conditions.append(ProviderVehicleDocument.vehicle_id == vehicle_id)

    stmt = (
        select(ProviderVehicleDocument)
        .where(*conditions)
        .order_by(ProviderVehicleDocument.created_at.asc())  # FIFO
        .limit(limit)
        .offset(offset)
    )
    docs = (await db.execute(stmt)).scalars().all()
    return [VehicleDocumentResponse.model_validate(d) for d in docs]


@router.post(
    "/vehicle-documents/{doc_id}/review",
    response_model=VehicleDocumentResponse,
)
async def admin_review_vehicle_document(
    doc_id: uuid.UUID,
    body: VehicleDocumentReviewRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> VehicleDocumentResponse:
    """Admin duyệt hoặc từ chối giấy tờ xe.

    Args:
        doc_id: UUID của giấy tờ.
        body: action = 'approved' hoặc 'rejected', kèm note khi rejected.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        VehicleDocumentResponse sau khi review.

    Raises:
        HTTPException 400: Nếu rejected mà không có note.
        HTTPException 404: Nếu giấy tờ không tìm thấy.
        HTTPException 409: Nếu giấy tờ đã được review rồi.
    """
    if body.action == "rejected" and not body.note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="note is required when rejecting a document",
        )

    doc = await db.get(ProviderVehicleDocument, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle document not found",
        )
    if doc.review_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document has already been reviewed (status: {doc.review_status})",
        )

    logger.info(
        "[ADMIN] Vehicle doc review - doc_id=%s action=%s admin=%s",
        doc.id, body.action, current_admin.id,
    )

    doc.review_status = body.action
    doc.reviewed_by = current_admin.id
    doc.reviewed_at = datetime.now(tz=timezone.utc)
    doc.review_note = body.note
    doc.updated_by = current_admin.id
    doc.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(doc)
    return VehicleDocumentResponse.model_validate(doc)


# ─────────────────────────────────────────────────────────────────────
# Admin — Routes
# ─────────────────────────────────────────────────────────────────────


@router.get("/routes", response_model=list[ServiceRouteResponse])
async def admin_list_routes(
    from_province: str | None = Query(default=None),
    to_province: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRouteResponse]:
    """Danh sách tất cả tuyến đường trong hệ thống.

    Args:
        from_province: Lọc tỉnh đi.
        to_province: Lọc tỉnh đến.
        is_active: Lọc trạng thái active.
        limit: Số bản ghi tối đa.
        offset: Pagination offset.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách ServiceRouteResponse kèm schedules.
    """
    conditions = []
    if from_province is not None:
        conditions.append(ServiceRoute.from_province.ilike(f"%{from_province}%"))
    if to_province is not None:
        conditions.append(ServiceRoute.to_province.ilike(f"%{to_province}%"))
    if is_active is not None:
        conditions.append(ServiceRoute.is_active == is_active)

    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(*conditions)
        .order_by(ServiceRoute.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    routes = (await db.execute(stmt)).scalars().all()
    return [ServiceRouteResponse.model_validate(r) for r in routes]


@router.get("/routes/{route_id}", response_model=ServiceRouteResponse)
async def admin_get_route(
    route_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Chi tiết tuyến đường kèm tất cả lịch khởi hành.

    Args:
        route_id: UUID của tuyến.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse kèm schedules.

    Raises:
        HTTPException 404: Nếu tuyến không tìm thấy.
    """
    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(ServiceRoute.id == route_id)
    )
    route = (await db.execute(stmt)).scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return ServiceRouteResponse.model_validate(route)


@router.patch("/routes/{route_id}/status", response_model=ServiceRouteResponse)
async def admin_patch_route_status(
    route_id: uuid.UUID,
    body: RouteStatusPatch,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceRouteResponse:
    """Admin bật / tắt tuyến đường (can thiệp khi có vi phạm).

    Args:
        route_id: UUID của tuyến.
        body: is_active mới.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        ServiceRouteResponse sau khi thay đổi.

    Raises:
        HTTPException 404: Nếu tuyến không tìm thấy.
    """
    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(ServiceRoute.id == route_id)
    )
    route = (await db.execute(stmt)).scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    logger.info(
        "[ADMIN] Route status change - route_id=%s is_active=%s admin=%s",
        route.id, body.is_active, current_admin.id,
    )

    route.is_active = body.is_active
    route.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(route)

    # Re-load with schedules
    stmt2 = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(ServiceRoute.id == route_id)
    )
    route = (await db.execute(stmt2)).scalar_one()
    return ServiceRouteResponse.model_validate(route)
