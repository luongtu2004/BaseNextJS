from __future__ import annotations

import logging
from typing import Any
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role, get_current_user
from app.db.session import get_db
from app.models.booking import CommissionConfig, PriceConfig
from app.schemas.booking import (
    CommissionConfigCreate,
    CommissionConfigResponse,
    CommissionConfigStatusPatch,
    CommissionConfigUpdate,
    PriceConfigCreate,
    PriceConfigResponse,
    PriceConfigStatusPatch,
    PriceConfigUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Admin / Pricing"],
    dependencies=[Depends(check_user_role("admin"))],
)


# ─────────────────────────────────────────────────────────────────────
# Price Configs
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/price-configs",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Danh sách cấu hình giá",
    description="Phân trang danh sách cấu hình giá (PriceConfig), lọc theo service_type.",
)
async def list_price_configs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service_type: str | None = None,
) -> dict[str, Any]:
    """Danh sách cấu hình giá.

    Args:
        db: Async DB session.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        service_type: Lọc theo loại dịch vụ.

    Returns:
        Dict phân trang chứa items (PriceConfigResponse), page, page_size, total.
    """
    base_stmt = select(PriceConfig)
    if service_type:
        base_stmt = base_stmt.where(PriceConfig.service_type == service_type)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    items_stmt = base_stmt.order_by(PriceConfig.created_at.desc()).offset(offset).limit(page_size)
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [PriceConfigResponse.model_validate(item).model_dump() for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/price-configs",
    response_model=PriceConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo cấu hình giá",
    description="Tạo PriceConfig mới. Tự động vô hiệu hóa cấu hình cũ cùng service_type.",
)
async def create_price_config(
    payload: PriceConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> PriceConfig:
    """Tạo cấu hình giá mới cho loại dịch vụ.

    Tự động đặt is_active=False cho tất cả cấu hình cũ cùng service_type.

    Args:
        payload: Thông tin cấu hình giá mới.
        db: Async DB session.

    Returns:
        PriceConfig mới được tạo.
    """
    # Set all old configs for this service to inactive
    old_configs = (await db.execute(
        select(PriceConfig).where(
            PriceConfig.service_type == payload.service_type,
            PriceConfig.is_active.is_(True)
        )
    )).scalars().all()

    now_utc = datetime.now(tz=timezone.utc)
    for c in old_configs:
        c.is_active = False
        c.effective_to = now_utc
        
    config = PriceConfig(**payload.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Price config created - config_id=%s service_type=%s mode=%s", config.id, config.service_type, config.pricing_mode)
    return config


@router.put(
    "/price-configs/{config_id}",
    response_model=PriceConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật cấu hình giá",
    description="Cập nhật các thuộc tính của một PriceConfig theo ID.",
)
async def update_price_config(
    config_id: uuid.UUID,
    payload: PriceConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> PriceConfig:
    """Cập nhật cấu hình giá theo ID.

    Args:
        config_id: UUID của cấu hình cần cập nhật.
        payload: Các trường cần thay đổi (exclude_unset).
        db: Async DB session.

    Returns:
        PriceConfig đã cập nhật.

    Raises:
        HTTPException 404: Nếu config không tồn tại.
    """
    config = (await db.execute(select(PriceConfig).where(PriceConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Price config not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(config, key, val)
        
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Price config updated - config_id=%s fields=%s", config_id, list(update_data.keys()))
    return config


@router.patch(
    "/price-configs/{config_id}/status",
    response_model=PriceConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật trạng thái cấu hình giá",
    description="Bật/tắt trạng thái hoạt động của PriceConfig.",
)
async def update_price_config_status(
    config_id: uuid.UUID,
    payload: PriceConfigStatusPatch,
    db: AsyncSession = Depends(get_db),
) -> PriceConfig:
    """Cập nhật trạng thái is_active của PriceConfig.

    Args:
        config_id: UUID của cấu hình giá.
        payload: Giá trị is_active mới.
        db: Async DB session.

    Returns:
        PriceConfig đã cập nhật.

    Raises:
        HTTPException 404: Nếu config không tồn tại.
    """
    config = (await db.execute(select(PriceConfig).where(PriceConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Price config not found")
        
    config.is_active = payload.is_active
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Price config status updated - config_id=%s is_active=%s", config_id, payload.is_active)
    return config


# ─────────────────────────────────────────────────────────────────────
# Commission Configs
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/commission-configs",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Danh sách cấu hình hoa hồng",
    description="Phân trang danh sách cấu hình hoa hồng (CommissionConfig), lọc theo service_type.",
)
async def list_commission_configs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service_type: str | None = None,
) -> dict[str, Any]:
    """Danh sách cấu hình hoa hồng.

    Args:
        db: Async DB session.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        service_type: Lọc theo loại dịch vụ.

    Returns:
        Dict phân trang chứa items (CommissionConfigResponse), page, page_size, total.
    """
    base_stmt = select(CommissionConfig)
    if service_type:
        base_stmt = base_stmt.where(CommissionConfig.service_type == service_type)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    items_stmt = base_stmt.order_by(CommissionConfig.created_at.desc()).offset(offset).limit(page_size)
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [CommissionConfigResponse.model_validate(item).model_dump() for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/commission-configs",
    response_model=CommissionConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo cấu hình hoa hồng",
    description="Tạo CommissionConfig mới. Tự động vô hiệu hóa cấu hình cũ cùng service_type.",
)
async def create_commission_config(
    payload: CommissionConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> CommissionConfig:
    """Tạo cấu hình hoa hồng mới cho loại dịch vụ.

    Tự động đặt is_active=False cho tất cả cấu hình cũ cùng service_type.

    Args:
        payload: Thông tin cấu hình hoa hồng mới.
        db: Async DB session.

    Returns:
        CommissionConfig mới được tạo.
    """
    # Set older active ones to false
    old_configs = (await db.execute(
        select(CommissionConfig).where(
            CommissionConfig.service_type == payload.service_type,
            CommissionConfig.is_active.is_(True)
        )
    )).scalars().all()

    now_utc = datetime.now(tz=timezone.utc)
    for c in old_configs:
        c.is_active = False
        c.effective_to = now_utc
        
    config = CommissionConfig(**payload.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Commission config created - config_id=%s service_type=%s rate=%s", config.id, config.service_type, config.rate_percent)
    return config


@router.put(
    "/commission-configs/{config_id}",
    response_model=CommissionConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật cấu hình hoa hồng",
    description="Cập nhật các thuộc tính của một CommissionConfig theo ID.",
)
async def update_commission_config(
    config_id: uuid.UUID,
    payload: CommissionConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> CommissionConfig:
    """Cập nhật cấu hình hoa hồng theo ID.

    Args:
        config_id: UUID của cấu hình cần cập nhật.
        payload: Các trường cần thay đổi (exclude_unset).
        db: Async DB session.

    Returns:
        CommissionConfig đã cập nhật.

    Raises:
        HTTPException 404: Nếu config không tồn tại.
    """
    config = (await db.execute(select(CommissionConfig).where(CommissionConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Commission config not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(config, key, val)
        
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Commission config updated - config_id=%s fields=%s", config_id, list(update_data.keys()))
    return config


@router.patch(
    "/commission-configs/{config_id}/status",
    response_model=CommissionConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật trạng thái hoa hồng",
    description="Bật/tắt trạng thái hoạt động của CommissionConfig.",
)
async def update_commission_config_status(
    config_id: uuid.UUID,
    payload: CommissionConfigStatusPatch,
    db: AsyncSession = Depends(get_db),
) -> CommissionConfig:
    """Cập nhật trạng thái is_active của CommissionConfig.

    Args:
        config_id: UUID của cấu hình hoa hồng.
        payload: Giá trị is_active mới.
        db: Async DB session.

    Returns:
        CommissionConfig đã cập nhật.

    Raises:
        HTTPException 404: Nếu config không tồn tại.
    """
    config = (await db.execute(select(CommissionConfig).where(CommissionConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Commission config not found")
        
    config.is_active = payload.is_active
    await db.commit()
    await db.refresh(config)
    logger.info("[ADMIN] Commission config status updated - config_id=%s is_active=%s", config_id, payload.is_active)
    return config
