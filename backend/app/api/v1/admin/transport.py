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
from app.models.provider import Provider, ProviderBusinessProfile, ProviderIndividualProfile
from app.models.provider_service import ProviderService
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleDocument,
    ServiceRoute,
)
from app.models.user import User
from app.schemas.transport import (
    AdminRouteListItem,
    AdminVehicleDocumentListItem,
    AdminVehicleListItem,
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


@router.get("/vehicles", response_model=dict)
async def admin_list_vehicles(
    provider_id: uuid.UUID | None = Query(default=None, description="Lọc theo provider"),
    vehicle_type: str | None = Query(default=None, description="Lọc theo loại xe"),
    status_filter: str | None = Query(default=None, alias="status", description="Lọc theo status"),
    license_plate: str | None = Query(default=None, description="Tìm theo biển số xe"),
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=50, ge=1, le=200, description="Kích thước trang"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Danh sách tất cả xe trong hệ thống. Hỗ trợ filter và pagination.

    Args:
        provider_id: Lọc theo provider cụ thể.
        vehicle_type: Lọc theo loại xe.
        status_filter: Lọc theo trạng thái (active/inactive/suspended).
        license_plate: Tìm theo biển số xe (ILIKE).
        page: Trang hiện tại.
        page_size: Kích thước trang.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách AdminVehicleListItem kèm provider_name.
    """
    conditions = []
    if provider_id is not None:
        conditions.append(ProviderVehicle.provider_id == provider_id)
    if vehicle_type is not None:
        conditions.append(ProviderVehicle.vehicle_type == vehicle_type)
    if status_filter is not None:
        conditions.append(ProviderVehicle.status == status_filter)
    if license_plate is not None:
        conditions.append(ProviderVehicle.license_plate.ilike(f"%{license_plate}%"))

    from sqlalchemy import func
    count_stmt = select(func.count(ProviderVehicle.id)).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ProviderVehicle)
        .where(*conditions)
        .order_by(ProviderVehicle.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    vehicles = (await db.execute(stmt)).scalars().all()

    if not vehicles:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # Bulk load provider profiles for provider_name
    prov_ids = list({v.provider_id for v in vehicles})
    prov_map: dict = {
        p.id: p
        for p in (await db.execute(
            select(Provider).where(Provider.id.in_(prov_ids))
        )).scalars().all()
    }
    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(prov_ids))
        )).scalars().all()
    }
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(prov_ids))
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
        prov = prov_map.get(v.provider_id)
        user = user_map.get(prov.owner_user_id) if prov and prov.owner_user_id else None
        provider_name = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(v.provider_id)
        )
        results.append(
            AdminVehicleListItem(
                id=v.id,
                provider_id=v.provider_id,
                provider_name=provider_name,
                owner_phone=user.phone if user else None,
                service_id=v.service_id,
                vehicle_type=v.vehicle_type,
                vehicle_brand=v.vehicle_brand,
                vehicle_model=v.vehicle_model,
                year_of_manufacture=v.year_of_manufacture,
                license_plate=v.license_plate,
                seat_count=v.seat_count,
                fuel_type=v.fuel_type,
                transmission=v.transmission,
                has_ac=v.has_ac,
                has_wifi=v.has_wifi,
                color=v.color,
                status=v.status,
                notes=v.notes,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
        )
    return {
        "items": results,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


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


@router.get("/vehicle-documents", response_model=dict)
async def admin_list_vehicle_documents(
    review_status: str | None = Query(
        default="pending", description="Lọc theo trạng thái duyệt: pending/approved/rejected"
    ),
    vehicle_id: uuid.UUID | None = Query(default=None, description="Lọc theo xe cụ thể"),
    provider_id: uuid.UUID | None = Query(default=None, description="Lọc theo provider"),
    document_type: str | None = Query(default=None, description="Lọc theo loại giấy tờ"),
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=50, ge=1, le=200, description="Số kết quả mỗi trang"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Queue giấy tờ xe chờ duyệt dành cho admin CMS.

    Args:
        review_status: Lọc theo trạng thái: pending (default), approved, rejected, hoặc None.
        vehicle_id: Lọc theo xe cụ thể.
        provider_id: Lọc theo provider.
        document_type: Lọc theo loại giấy tờ.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách AdminVehicleDocumentListItem kèm thông tin xe và provider.
    """
    conditions = []
    if review_status is not None:
        conditions.append(ProviderVehicleDocument.review_status == review_status)
    if vehicle_id is not None:
        conditions.append(ProviderVehicleDocument.vehicle_id == vehicle_id)
    if document_type is not None:
        conditions.append(ProviderVehicleDocument.document_type == document_type)

    # If filtering by provider_id, find their vehicle IDs first
    if provider_id is not None:
        veh_ids_stmt = select(ProviderVehicle.id).where(ProviderVehicle.provider_id == provider_id)
        veh_ids = [r for r in (await db.execute(veh_ids_stmt)).scalars().all()]
        conditions.append(ProviderVehicleDocument.vehicle_id.in_(veh_ids))

    from sqlalchemy import func
    count_stmt = select(func.count(ProviderVehicleDocument.id)).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ProviderVehicleDocument)
        .where(*conditions)
        .order_by(ProviderVehicleDocument.created_at.asc())  # FIFO
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    docs = (await db.execute(stmt)).scalars().all()

    if not docs:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # Bulk load vehicle + provider info
    veh_ids = list({d.vehicle_id for d in docs})
    veh_map: dict = {
        v.id: v
        for v in (await db.execute(
            select(ProviderVehicle).where(ProviderVehicle.id.in_(veh_ids))
        )).scalars().all()
    }
    prov_ids = list({v.provider_id for v in veh_map.values()})
    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(prov_ids))
        )).scalars().all()
    } if prov_ids else {}
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(prov_ids))
        )).scalars().all()
    } if prov_ids else {}

    results = []
    for d in docs:
        veh = veh_map.get(d.vehicle_id)
        pid = veh.provider_id if veh else None
        biz = biz_map.get(pid) if pid else None
        ind = ind_map.get(pid) if pid else None
        pname = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or (str(pid) if pid else None)
        )
        results.append(
            AdminVehicleDocumentListItem(
                id=d.id,
                vehicle_id=d.vehicle_id,
                vehicle_license_plate=veh.license_plate if veh else None,
                vehicle_type=veh.vehicle_type if veh else None,
                provider_id=pid,
                provider_name=pname,
                document_type=d.document_type,
                document_number=d.document_number,
                issued_date=d.issued_date,
                expiry_date=d.expiry_date,
                file_url=d.file_url,
                review_status=d.review_status,
                reviewed_by=d.reviewed_by,
                reviewed_at=d.reviewed_at,
                review_note=d.review_note,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
        )
    return {
        "items": results,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


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


@router.get("/routes", response_model=dict)
async def admin_list_routes(
    from_province: str | None = Query(default=None),
    to_province: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    provider_id: uuid.UUID | None = Query(default=None, description="Lọc theo provider"),
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=50, ge=1, le=200, description="Kích thước trang"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Danh sách tất cả tuyến đường trong hệ thống.

    Args:
        from_province: Lọc tỉnh đi.
        to_province: Lọc tỉnh đến.
        is_active: Lọc trạng thái active.
        provider_id: Lọc theo provider.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách AdminRouteListItem kèm provider_name và schedules.
    """
    conditions = []
    if from_province is not None:
        conditions.append(ServiceRoute.from_province.ilike(f"%{from_province}%"))
    if to_province is not None:
        conditions.append(ServiceRoute.to_province.ilike(f"%{to_province}%"))
    if is_active is not None:
        conditions.append(ServiceRoute.is_active == is_active)
    if provider_id is not None:
        svc_ids_stmt = select(ProviderService.id).where(ProviderService.provider_id == provider_id)
        svc_ids = [r for r in (await db.execute(svc_ids_stmt)).scalars().all()]
        conditions.append(ServiceRoute.provider_service_id.in_(svc_ids))

    from sqlalchemy import func
    count_stmt = select(func.count(ServiceRoute.id)).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ServiceRoute)
        .options(selectinload(ServiceRoute.schedules))
        .where(*conditions)
        .order_by(ServiceRoute.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    routes = (await db.execute(stmt)).scalars().all()

    if not routes:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # Bulk load provider info
    svc_ids = list({r.provider_service_id for r in routes})
    svc_map: dict = {
        s.id: s
        for s in (await db.execute(
            select(ProviderService).where(ProviderService.id.in_(svc_ids))
        )).scalars().all()
    }
    prov_ids = list({s.provider_id for s in svc_map.values()})
    biz_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderBusinessProfile).where(ProviderBusinessProfile.provider_id.in_(prov_ids))
        )).scalars().all()
    } if prov_ids else {}
    ind_map: dict = {
        p.provider_id: p
        for p in (await db.execute(
            select(ProviderIndividualProfile).where(ProviderIndividualProfile.provider_id.in_(prov_ids))
        )).scalars().all()
    } if prov_ids else {}

    results = []
    for r in routes:
        svc = svc_map.get(r.provider_service_id)
        pid = svc.provider_id if svc else None
        biz = biz_map.get(pid) if pid else None
        ind = ind_map.get(pid) if pid else None
        pname = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or (str(pid) if pid else None)
        )
        item = AdminRouteListItem.model_validate(r)
        item.provider_id = pid
        item.provider_name = pname
        results.append(item)
    return {
        "items": results,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/routes/{route_id}", response_model=AdminRouteListItem)
async def admin_get_route(
    route_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminRouteListItem:
    """Chi tiết tuyến đường kèm tất cả lịch khởi hành.

    Args:
        route_id: UUID của tuyến.
        current_admin: Admin đang đăng nhập.
        db: Async DB session.

    Returns:
        AdminRouteListItem kèm schedules và provider_name.

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

    # Load provider info
    svc = await db.get(ProviderService, route.provider_service_id)
    pid = svc.provider_id if svc else None
    pname = str(pid) if pid else None
    if pid:
        biz = await db.get(ProviderBusinessProfile, pid)
        ind = await db.get(ProviderIndividualProfile, pid)
        pname = (
            (biz.company_name if biz else None)
            or (ind.full_name if ind else None)
            or str(pid)
        )

    item = AdminRouteListItem.model_validate(route)
    item.provider_id = pid
    item.provider_name = pname
    return item


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
