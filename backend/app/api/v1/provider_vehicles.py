"""Provider API — Quản lý phương tiện (Phase 6.2).

Endpoints:
  POST   /provider/vehicles
  GET    /provider/vehicles
  GET    /provider/vehicles/{id}
  PUT    /provider/vehicles/{id}
  PATCH  /provider/vehicles/{id}/status
  DELETE /provider/vehicles/{id}
  POST   /provider/vehicles/{id}/documents
  GET    /provider/vehicles/{id}/documents
  GET    /provider/vehicles/{id}/documents/{doc_id}
  PUT    /provider/vehicles/{id}/documents/{doc_id}
  DELETE /provider/vehicles/{id}/documents/{doc_id}
  GET    /provider/vehicles/{id}/availabilities
  POST   /provider/vehicles/{id}/availabilities/block
  POST   /provider/vehicles/{id}/availabilities/unblock
"""

import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.provider import Provider
from app.models.provider_service import ProviderService
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleAvailability,
    ProviderVehicleDocument,
)
from app.models.user import User
from app.schemas.transport import (
    AvailabilityBlockRequest,
    AvailabilityItem,
    AvailabilityUnblockRequest,
    ProviderVehicleCreate,
    ProviderVehicleResponse,
    ProviderVehicleUpdate,
    VehicleAvailabilityResponse,
    VehicleDocumentCreate,
    VehicleDocumentResponse,
    VehicleDocumentUpdate,
    VehicleStatusPatch,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/provider/vehicles", tags=["provider-vehicles"])


# ─────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────


async def _get_provider_or_403(
    current_user: User,
    db: AsyncSession,
) -> Provider:
    """Lấy Provider của user hiện tại hoặc raise 403.

    Args:
        current_user: User từ JWT token.
        db: Async DB session.

    Returns:
        Provider record thuộc về current_user.

    Raises:
        HTTPException 403: Nếu user chưa có hồ sơ provider.
    """
    stmt = select(Provider).where(Provider.owner_user_id == current_user.id)
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a service provider",
        )
    return provider


async def _get_vehicle_or_404(
    vehicle_id: uuid.UUID,
    provider_id: uuid.UUID,
    db: AsyncSession,
) -> ProviderVehicle:
    """Lấy xe theo ID và validate ownership.

    Args:
        vehicle_id: UUID của xe.
        provider_id: UUID của provider sở hữu xe.
        db: Async DB session.

    Returns:
        ProviderVehicle record.

    Raises:
        HTTPException 404: Nếu xe không tồn tại hoặc không thuộc provider.
    """
    stmt = select(ProviderVehicle).where(
        and_(
            ProviderVehicle.id == vehicle_id,
            ProviderVehicle.provider_id == provider_id,
        )
    )
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return vehicle


async def _get_doc_or_404(
    doc_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    db: AsyncSession,
) -> ProviderVehicleDocument:
    """Lấy giấy tờ xe theo ID và validate thuộc đúng xe.

    Args:
        doc_id: UUID của giấy tờ.
        vehicle_id: UUID của xe chứa giấy tờ.
        db: Async DB session.

    Returns:
        ProviderVehicleDocument record.

    Raises:
        HTTPException 404: Nếu giấy tờ không tồn tại.
    """
    stmt = select(ProviderVehicleDocument).where(
        and_(
            ProviderVehicleDocument.id == doc_id,
            ProviderVehicleDocument.vehicle_id == vehicle_id,
        )
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle document not found",
        )
    return doc


# ─────────────────────────────────────────────────────────────────────
# Vehicle CRUD
# ─────────────────────────────────────────────────────────────────────


@router.post("", response_model=ProviderVehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    body: ProviderVehicleCreate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Thêm xe mới cho provider.

    Args:
        body: Thông tin xe.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse của xe vừa tạo.

    Raises:
        HTTPException 403: Nếu user không có hồ sơ provider.
        HTTPException 404: Nếu service_id không thuộc provider.
    """
    provider = await _get_provider_or_403(current_user, db)

    # Validate service_id belongs to this provider
    if body.service_id is not None:
        svc_stmt = select(ProviderService).where(
            and_(
                ProviderService.id == body.service_id,
                ProviderService.provider_id == provider.id,
            )
        )
        svc = (await db.execute(svc_stmt)).scalar_one_or_none()
        if not svc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or does not belong to this provider",
            )

    logger.info("[VEHICLE] Creating vehicle - provider_id=%s type=%s", provider.id, body.vehicle_type)

    vehicle = ProviderVehicle(
        provider_id=provider.id,
        service_id=body.service_id,
        vehicle_type=body.vehicle_type,
        vehicle_brand=body.vehicle_brand,
        vehicle_model=body.vehicle_model,
        year_of_manufacture=body.year_of_manufacture,
        license_plate=body.license_plate,
        seat_count=body.seat_count,
        fuel_type=body.fuel_type,
        transmission=body.transmission,
        has_ac=body.has_ac,
        has_wifi=body.has_wifi,
        color=body.color,
        notes=body.notes,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    logger.info("[VEHICLE] Vehicle created - vehicle_id=%s", vehicle.id)
    return ProviderVehicleResponse.model_validate(vehicle)


@router.get("", response_model=list[ProviderVehicleResponse])
async def list_vehicles(
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderVehicleResponse]:
    """Danh sách xe của provider đang đăng nhập.

    Args:
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách ProviderVehicleResponse.
    """
    provider = await _get_provider_or_403(current_user, db)

    stmt = (
        select(ProviderVehicle)
        .where(ProviderVehicle.provider_id == provider.id)
        .order_by(ProviderVehicle.created_at.desc())
    )
    result = await db.execute(stmt)
    vehicles = result.scalars().all()
    return [ProviderVehicleResponse.model_validate(v) for v in vehicles]


@router.get("/{vehicle_id}", response_model=ProviderVehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Chi tiết một xe của provider.

    Args:
        vehicle_id: UUID của xe cần xem.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse.

    Raises:
        HTTPException 404: Nếu xe không tồn tại hoặc không thuộc provider.
    """
    provider = await _get_provider_or_403(current_user, db)
    vehicle = await _get_vehicle_or_404(vehicle_id, provider.id, db)
    return ProviderVehicleResponse.model_validate(vehicle)


@router.put("/{vehicle_id}", response_model=ProviderVehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    body: ProviderVehicleUpdate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Cập nhật thông tin xe.

    Args:
        vehicle_id: UUID của xe.
        body: Các trường cần cập nhật (chỉ trường có giá trị mới được update).
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse sau khi cập nhật.

    Raises:
        HTTPException 404: Nếu xe hoặc service_id không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    vehicle = await _get_vehicle_or_404(vehicle_id, provider.id, db)

    # Validate service_id if provided
    if body.service_id is not None:
        svc_stmt = select(ProviderService).where(
            and_(
                ProviderService.id == body.service_id,
                ProviderService.provider_id == provider.id,
            )
        )
        svc = (await db.execute(svc_stmt)).scalar_one_or_none()
        if not svc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or does not belong to this provider",
            )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    vehicle.updated_by = current_user.id
    vehicle.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(vehicle)
    return ProviderVehicleResponse.model_validate(vehicle)


@router.patch("/{vehicle_id}/status", response_model=ProviderVehicleResponse)
async def patch_vehicle_status(
    vehicle_id: uuid.UUID,
    body: VehicleStatusPatch,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> ProviderVehicleResponse:
    """Kích hoạt hoặc tạm ngừng xe.

    Args:
        vehicle_id: UUID của xe.
        body: status mới (active | inactive).
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        ProviderVehicleResponse sau khi thay đổi status.

    Raises:
        HTTPException 404: Nếu xe không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    vehicle = await _get_vehicle_or_404(vehicle_id, provider.id, db)

    logger.info(
        "[VEHICLE] Status change - vehicle_id=%s old=%s new=%s",
        vehicle.id, vehicle.status, body.status,
    )

    vehicle.status = body.status
    vehicle.updated_by = current_user.id
    vehicle.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(vehicle)
    return ProviderVehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Xóa xe. Tất cả giấy tờ và lịch availability sẽ bị xóa theo (cascade).

    Args:
        vehicle_id: UUID của xe cần xóa.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Raises:
        HTTPException 404: Nếu xe không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    vehicle = await _get_vehicle_or_404(vehicle_id, provider.id, db)

    logger.info("[VEHICLE] Deleting vehicle - vehicle_id=%s provider_id=%s", vehicle.id, provider.id)
    await db.delete(vehicle)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────
# Vehicle Documents
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/{vehicle_id}/documents",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_vehicle_document(
    vehicle_id: uuid.UUID,
    body: VehicleDocumentCreate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> VehicleDocumentResponse:
    """Thêm giấy tờ pháp lý cho xe.

    Args:
        vehicle_id: UUID của xe.
        body: Thông tin giấy tờ.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        VehicleDocumentResponse vừa tạo.

    Raises:
        HTTPException 400: Nếu expiry_date trước issued_date.
    """
    provider = await _get_provider_or_403(current_user, db)
    vehicle = await _get_vehicle_or_404(vehicle_id, provider.id, db)

    # Validate date logic
    if body.issued_date and body.expiry_date and body.expiry_date <= body.issued_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expiry_date must be after issued_date",
        )

    doc = ProviderVehicleDocument(
        vehicle_id=vehicle.id,
        document_type=body.document_type,
        document_number=body.document_number,
        issued_date=body.issued_date,
        expiry_date=body.expiry_date,
        file_url=body.file_url,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return VehicleDocumentResponse.model_validate(doc)


@router.get("/{vehicle_id}/documents", response_model=list[VehicleDocumentResponse])
async def list_vehicle_documents(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> list[VehicleDocumentResponse]:
    """Danh sách giấy tờ của một xe.

    Args:
        vehicle_id: UUID của xe.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Danh sách VehicleDocumentResponse.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)

    stmt = (
        select(ProviderVehicleDocument)
        .where(ProviderVehicleDocument.vehicle_id == vehicle_id)
        .order_by(ProviderVehicleDocument.created_at.desc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [VehicleDocumentResponse.model_validate(d) for d in docs]


@router.get("/{vehicle_id}/documents/{doc_id}", response_model=VehicleDocumentResponse)
async def get_vehicle_document(
    vehicle_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> VehicleDocumentResponse:
    """Chi tiết một giấy tờ xe.

    Args:
        vehicle_id: UUID của xe.
        doc_id: UUID của giấy tờ.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        VehicleDocumentResponse.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)
    doc = await _get_doc_or_404(doc_id, vehicle_id, db)
    return VehicleDocumentResponse.model_validate(doc)


@router.put("/{vehicle_id}/documents/{doc_id}", response_model=VehicleDocumentResponse)
async def update_vehicle_document(
    vehicle_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: VehicleDocumentUpdate,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> VehicleDocumentResponse:
    """Cập nhật giấy tờ xe (provider chỉnh sửa trước khi duyệt).

    Args:
        vehicle_id: UUID của xe.
        doc_id: UUID của giấy tờ.
        body: Thông tin cần cập nhật.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        VehicleDocumentResponse sau khi cập nhật.

    Raises:
        HTTPException 400: Nếu expiry_date không hợp lệ hoặc giấy tờ đã được duyệt.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)
    doc = await _get_doc_or_404(doc_id, vehicle_id, db)

    if doc.review_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit an already approved document",
        )

    # Determine final dates after update
    final_issued = body.issued_date if body.issued_date is not None else doc.issued_date
    final_expiry = body.expiry_date if body.expiry_date is not None else doc.expiry_date
    if final_issued and final_expiry and final_expiry <= final_issued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expiry_date must be after issued_date",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    # Reset review status to pending since doc was modified
    doc.review_status = "pending"
    doc.reviewed_by = None
    doc.reviewed_at = None
    doc.review_note = None
    doc.updated_by = current_user.id
    doc.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(doc)
    return VehicleDocumentResponse.model_validate(doc)


@router.delete("/{vehicle_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_document(
    vehicle_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Xóa giấy tờ xe.

    Args:
        vehicle_id: UUID của xe.
        doc_id: UUID của giấy tờ.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Raises:
        HTTPException 404: Nếu giấy tờ không tìm thấy.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)
    doc = await _get_doc_or_404(doc_id, vehicle_id, db)
    await db.delete(doc)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────
# Vehicle Availabilities
# ─────────────────────────────────────────────────────────────────────


@router.get("/{vehicle_id}/availabilities", response_model=VehicleAvailabilityResponse)
async def get_vehicle_availabilities(
    vehicle_id: uuid.UUID,
    from_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> VehicleAvailabilityResponse:
    """Xem lịch availability của xe trong khoảng thời gian.

    Args:
        vehicle_id: UUID của xe.
        from_date: Ngày bắt đầu.
        to_date: Ngày kết thúc.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        VehicleAvailabilityResponse chứa danh sách ngày bị block.

    Raises:
        HTTPException 400: Nếu from_date > to_date.
    """
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before or equal to to_date",
        )

    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)

    stmt = (
        select(ProviderVehicleAvailability)
        .where(
            and_(
                ProviderVehicleAvailability.vehicle_id == vehicle_id,
                ProviderVehicleAvailability.date >= from_date,
                ProviderVehicleAvailability.date <= to_date,
            )
        )
        .order_by(ProviderVehicleAvailability.date)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return VehicleAvailabilityResponse(
        vehicle_id=vehicle_id,
        items=[AvailabilityItem.model_validate(i) for i in items],
    )


@router.post("/{vehicle_id}/availabilities/block", status_code=status.HTTP_200_OK)
async def block_vehicle_dates(
    vehicle_id: uuid.UUID,
    body: AvailabilityBlockRequest,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Block các ngày không cho thuê xe.

    Nếu ngày đã có record: giữ nguyên (idempotent).
    Nếu chưa có: tạo record mới với is_blocked=True.

    Args:
        vehicle_id: UUID của xe.
        body: Danh sách ngày và lý do block.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Dict với blocked_count.

    Raises:
        HTTPException 400: Nếu ngày trong quá khứ.
    """
    today = date.today()
    past_dates = [d for d in body.dates if d < today]
    if past_dates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot block past dates: {[str(d) for d in past_dates]}",
        )

    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)

    # Fetch existing records for the requested dates
    stmt = select(ProviderVehicleAvailability).where(
        and_(
            ProviderVehicleAvailability.vehicle_id == vehicle_id,
            ProviderVehicleAvailability.date.in_(body.dates),
        )
    )
    existing = {row.date: row for row in (await db.execute(stmt)).scalars().all()}

    blocked_count = 0
    for d in body.dates:
        if d in existing:
            # Update reason if already blocked
            existing[d].is_blocked = True
            existing[d].blocked_reason = body.reason
        else:
            db.add(ProviderVehicleAvailability(
                vehicle_id=vehicle_id,
                date=d,
                is_blocked=True,
                blocked_reason=body.reason,
            ))
            blocked_count += 1

    await db.commit()
    return {"blocked_count": blocked_count, "updated_count": len(existing)}


@router.post("/{vehicle_id}/availabilities/unblock", status_code=status.HTTP_200_OK)
async def unblock_vehicle_dates(
    vehicle_id: uuid.UUID,
    body: AvailabilityUnblockRequest,
    current_user: User = Depends(check_user_role("provider_owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mở lại các ngày đã bị block.

    Xóa hoàn toàn các records blocked để ngày trở về trạng thái rảnh.

    Args:
        vehicle_id: UUID của xe.
        body: Danh sách ngày cần unblock.
        current_user: Provider đang đăng nhập.
        db: Async DB session.

    Returns:
        Dict với unblocked_count.
    """
    provider = await _get_provider_or_403(current_user, db)
    await _get_vehicle_or_404(vehicle_id, provider.id, db)

    stmt = select(ProviderVehicleAvailability).where(
        and_(
            ProviderVehicleAvailability.vehicle_id == vehicle_id,
            ProviderVehicleAvailability.date.in_(body.dates),
            ProviderVehicleAvailability.is_blocked == True,  # noqa: E712
        )
    )
    records = (await db.execute(stmt)).scalars().all()

    count = len(records)
    for rec in records:
        await db.delete(rec)

    await db.commit()
    return {"unblocked_count": count}
