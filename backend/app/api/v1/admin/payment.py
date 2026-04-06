"""Admin API — Payment, Finance & Promotions (Phase 8).

Endpoints:
  GET    /admin/wallets                         DS ví (phân trang)
  GET    /admin/wallets/{user_id}               Ví + giao dịch của user
  POST   /admin/wallets/{user_id}/adjust        Điều chỉnh số dư thủ công
  GET    /admin/finance/revenue                 Doanh thu nền tảng theo ngày
  POST   /admin/withdrawals/{txn_id}/approve    Duyệt rút tiền
  POST   /admin/withdrawals/{txn_id}/reject     Từ chối rút tiền
  GET    /admin/promotions                      DS khuyến mãi
  POST   /admin/promotions                      Tạo khuyến mãi
  PUT    /admin/promotions/{id}                 Cập nhật khuyến mãi
  PATCH  /admin/promotions/{id}/status          Bật/tắt khuyến mãi
  GET    /admin/promotions/{id}/usages          Lịch sử dùng
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.payment import (
    Promotion,
    PromotionUsage,
    Wallet,
    WalletTransaction,
)
from app.models.user import User
from app.schemas.payment import (
    PromotionCreate,
    PromotionResponse,
    PromotionStatusPatch,
    PromotionUpdate,
    PromotionUsageResponse,
    RevenueResponse,
    WalletAdjustRequest,
    WalletResponse,
    WalletTransactionResponse,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Admin / Payment & Finance"],
    dependencies=[Depends(check_user_role("admin"))],
)


# ─────────────────────────────────────────────────────────────────────
# Wallets
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/wallets",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Danh sách ví",
    description="Admin xem danh sách tất cả ví, hỗ trợ lọc theo is_frozen.",
)
async def admin_list_wallets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_frozen: bool | None = Query(None, description="Lọc theo trạng thái đóng băng"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Danh sách tất cả ví.

    Args:
        page: Trang hiện tại.
        page_size: Kích thước trang.
        is_frozen: Lọc theo trạng thái đóng băng.
        db: Async DB session.

    Returns:
        Dict phân trang chứa items (WalletResponse), page, page_size, total.
    """
    base_stmt = select(Wallet)
    if is_frozen is not None:
        base_stmt = base_stmt.where(Wallet.is_frozen == is_frozen)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(Wallet.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [WalletResponse.model_validate(w) for w in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/wallets/{user_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Chi tiết ví theo user",
    description="Admin xem ví và 50 giao dịch gần nhất của một user.",
)
async def admin_get_wallet_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Chi tiết ví kèm giao dịch gần nhất.

    Args:
        user_id: UUID của user.
        db: Async DB session.

    Returns:
        Dict gồm wallet (WalletResponse) và transactions.

    Raises:
        HTTPException 404: Nếu user chưa có ví.
    """
    wallet = (
        await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
    ).scalars().first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found for this user")

    txns = (
        await db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    return {
        "wallet": WalletResponse.model_validate(wallet),
        "transactions": [WalletTransactionResponse.model_validate(t) for t in txns],
    }


@router.post(
    "/wallets/{user_id}/adjust",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Điều chỉnh số dư",
    description="Admin điều chỉnh số dư ví thủ công (bonus hoặc phạt).",
)
async def admin_adjust_wallet(
    user_id: uuid.UUID,
    payload: WalletAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> WalletResponse:
    """Điều chỉnh số dư ví.

    amount > 0: bonus/credit.
    amount < 0: phạt/debit (check balance).

    Args:
        user_id: UUID của user cần điều chỉnh.
        payload: Số tiền và lý do.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        WalletResponse sau khi điều chỉnh.

    Raises:
        HTTPException 400: Nếu amount=0 hoặc số dư không đủ.
    """
    if payload.amount == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero")

    try:
        wallet = await PaymentService.get_or_create_wallet(db, user_id)

        if payload.amount > 0:
            await PaymentService.credit_wallet(
                db, wallet, payload.amount,
                txn_type="adjust",
                reference_type="admin_adjust",
                description=payload.description,
            )
        else:
            await PaymentService.debit_wallet(
                db, wallet, abs(payload.amount),
                txn_type="adjust",
                reference_type="admin_adjust",
                description=payload.description,
            )

        await db.commit()
        await db.refresh(wallet)
        logger.info(
            "[ADMIN] Wallet adjusted - user_id=%s amount=%s by admin=%s",
            user_id, payload.amount, current_admin.id,
        )
        return WalletResponse.model_validate(wallet)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error adjusting wallet: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to adjust wallet: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# Finance / Revenue
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/finance/revenue",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Doanh thu nền tảng",
    description="Thống kê doanh thu (hoa hồng thu được) theo ngày.",
)
async def admin_get_revenue(
    days: int = Query(30, ge=1, le=365, description="Số ngày thống kê"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Thống kê doanh thu nền tảng theo ngày.

    NOTE: Chỉ tính commission từ các booking cash (driver ví bị trừ commission).
    Commission từ online payment không được ghi vào wallet_transactions vì
    platform thu trực tiếp qua payment gateway — cần platform wallet để track đầy đủ.

    Args:
        days: Số ngày lấy thống kê.
        db: Async DB session.

    Returns:
        Dict chứa items (RevenueResponse) và tổng hợp.
    """
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    date_col = cast(WalletTransaction.created_at, Date)

    rows = (
        await db.execute(
            select(
                date_col.label("date"),
                func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0).label("total_commission"),
                func.count().label("total_trips"),
            ).where(
                WalletTransaction.type == "commission",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= since,
            ).group_by(date_col).order_by(date_col.desc())
        )
    ).all()

    items = [
        RevenueResponse(
            date=str(row.date),
            total_commission=float(row.total_commission),
            total_trips=row.total_trips,
            total_fare=0,  # Cần join booking để có total_fare — MVP trả 0
        )
        for row in rows
    ]

    grand_total = sum(item.total_commission for item in items)

    return {
        "items": items,
        "total_commission": grand_total,
        "total_trips": sum(item.total_trips for item in items),
        "days": days,
    }


# ─────────────────────────────────────────────────────────────────────
# Withdrawals
# ─────────────────────────────────────────────────────────────────────

@router.post(
    "/withdrawals/{txn_id}/approve",
    response_model=WalletTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Duyệt rút tiền",
    description="Admin duyệt yêu cầu rút tiền. Balance đã bị hold từ lúc tạo request.",
)
async def admin_approve_withdrawal(
    txn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> WalletTransactionResponse:
    """Duyệt yêu cầu rút tiền.

    Balance đã bị hold từ lúc tạo request — chỉ cần update status.

    Args:
        txn_id: UUID của WalletTransaction (withdrawal pending).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        WalletTransactionResponse với status='completed'.

    Raises:
        HTTPException 404: Nếu không tìm thấy pending withdrawal.
    """
    try:
        txn = (
            await db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.id == txn_id,
                    WalletTransaction.type == "withdrawal",
                    WalletTransaction.status == "pending",
                )
            )
        ).scalars().first()

        if not txn:
            raise HTTPException(status_code=404, detail="Pending withdrawal not found")

        txn.status = "completed"
        now = datetime.now(tz=timezone.utc).isoformat()
        txn.description = f"{txn.description or ''} | Approved by admin {current_admin.id} at {now}" if txn.description else f"Approved by admin {current_admin.id} at {now}"
        await db.commit()
        await db.refresh(txn)

        logger.info("[ADMIN] Withdrawal approved - txn_id=%s by admin=%s", txn_id, current_admin.id)
        return WalletTransactionResponse.model_validate(txn)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error approving withdrawal: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to approve withdrawal: {str(e)}")


@router.post(
    "/withdrawals/{txn_id}/reject",
    response_model=WalletTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Từ chối rút tiền",
    description="Admin từ chối yêu cầu rút tiền. Hoàn lại balance cho tài xế.",
)
async def admin_reject_withdrawal(
    txn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> WalletTransactionResponse:
    """Từ chối yêu cầu rút tiền — hoàn lại balance.

    Tạo thêm WalletTransaction(type='refund') để ghi nhận hoàn tiền.

    Args:
        txn_id: UUID của WalletTransaction (withdrawal pending).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        WalletTransactionResponse của withdrawal gốc (status='failed').

    Raises:
        HTTPException 404: Nếu không tìm thấy pending withdrawal.
    """
    try:
        txn = (
            await db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.id == txn_id,
                    WalletTransaction.type == "withdrawal",
                    WalletTransaction.status == "pending",
                )
            )
        ).scalars().first()

        if not txn:
            raise HTTPException(status_code=404, detail="Pending withdrawal not found")

        txn.status = "failed"

        # Hoàn lại balance — dùng row-level lock để tránh race condition
        wallet = (
            await db.execute(
                select(Wallet).where(Wallet.id == txn.wallet_id).with_for_update()
            )
        ).scalars().first()
        if wallet:
            refund_amount = Decimal(str(abs(float(txn.amount))))
            wallet.balance = Decimal(str(wallet.balance)) + refund_amount
            wallet.updated_at = datetime.now(tz=timezone.utc)

            refund_txn = WalletTransaction(
                wallet_id=wallet.id,
                type="refund",
                amount=float(refund_amount),
                balance_after=float(wallet.balance),
                reference_id=txn.id,
                reference_type="withdrawal_refund",
                description="Withdrawal rejected - refund",
                status="completed",
            )
            db.add(refund_txn)

        await db.commit()
        await db.refresh(txn)

        logger.info(
            "[ADMIN] Withdrawal rejected - txn_id=%s refunded=%s by admin=%s",
            txn_id, abs(float(txn.amount)), current_admin.id,
        )
        return WalletTransactionResponse.model_validate(txn)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error rejecting withdrawal: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to reject withdrawal: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# Promotions
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/promotions",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Danh sách khuyến mãi",
    description="Admin xem danh sách tất cả chương trình khuyến mãi.",
)
async def admin_list_promotions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None, description="Lọc theo trạng thái"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Danh sách tất cả khuyến mãi.

    Args:
        page: Trang hiện tại.
        page_size: Kích thước trang.
        is_active: Lọc theo trạng thái.
        db: Async DB session.

    Returns:
        Dict phân trang chứa items (PromotionResponse), page, page_size, total.
    """
    base_stmt = select(Promotion)
    if is_active is not None:
        base_stmt = base_stmt.where(Promotion.is_active == is_active)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(Promotion.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [PromotionResponse.model_validate(p) for p in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/promotions",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo khuyến mãi",
    description="Admin tạo chương trình khuyến mãi mới.",
)
async def admin_create_promotion(
    payload: PromotionCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> PromotionResponse:
    """Tạo chương trình khuyến mãi.

    Args:
        payload: Thông tin khuyến mãi.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        PromotionResponse mới tạo.

    Raises:
        HTTPException 409: Nếu code đã tồn tại.
        HTTPException 400: Nếu valid_to <= valid_from.
    """
    if payload.valid_to <= payload.valid_from:
        raise HTTPException(status_code=400, detail="valid_to must be after valid_from")

    try:
        # Check code uniqueness
        existing = (
            await db.execute(
                select(Promotion).where(Promotion.code == payload.code).limit(1)
            )
        ).scalars().first()
        if existing:
            raise HTTPException(status_code=409, detail="Promotion code already exists")

        promo = Promotion(**payload.model_dump())
        db.add(promo)
        await db.commit()
        await db.refresh(promo)

        logger.info("[ADMIN] Promotion created - code=%s by admin=%s", promo.code, current_admin.id)
        return PromotionResponse.model_validate(promo)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error creating promotion: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to create promotion: {str(e)}")


@router.put(
    "/promotions/{promotion_id}",
    response_model=PromotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật khuyến mãi",
    description="Admin cập nhật thông tin khuyến mãi.",
)
async def admin_update_promotion(
    promotion_id: uuid.UUID,
    payload: PromotionUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> PromotionResponse:
    """Cập nhật khuyến mãi.

    Args:
        promotion_id: UUID của promotion.
        payload: Các trường cần cập nhật (exclude_unset).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        PromotionResponse đã cập nhật.

    Raises:
        HTTPException 404: Nếu promotion không tồn tại.
        HTTPException 400: Nếu valid_to <= valid_from sau khi cập nhật.
    """
    try:
        promo = await db.get(Promotion, promotion_id)
        if not promo:
            raise HTTPException(status_code=404, detail="Promotion not found")

        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(promo, key, val)

        # Validate date range sau khi cập nhật
        if promo.valid_to <= promo.valid_from:
            raise HTTPException(status_code=400, detail="valid_to must be after valid_from")

        promo.updated_at = datetime.now(tz=timezone.utc)
        await db.commit()
        await db.refresh(promo)

        logger.info(
            "[ADMIN] Promotion updated - id=%s fields=%s by admin=%s",
            promotion_id, list(update_data.keys()), current_admin.id,
        )
        return PromotionResponse.model_validate(promo)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error updating promotion: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to update promotion: {str(e)}")


@router.patch(
    "/promotions/{promotion_id}/status",
    response_model=PromotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Bật/tắt khuyến mãi",
    description="Admin bật hoặc tắt chương trình khuyến mãi.",
)
async def admin_toggle_promotion(
    promotion_id: uuid.UUID,
    payload: PromotionStatusPatch,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(check_user_role("admin")),
) -> PromotionResponse:
    """Bật/tắt khuyến mãi.

    Args:
        promotion_id: UUID của promotion.
        payload: Giá trị is_active mới.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        PromotionResponse đã cập nhật.

    Raises:
        HTTPException 404: Nếu promotion không tồn tại.
    """
    try:
        promo = await db.get(Promotion, promotion_id)
        if not promo:
            raise HTTPException(status_code=404, detail="Promotion not found")

        promo.is_active = payload.is_active
        promo.updated_at = datetime.now(tz=timezone.utc)
        await db.commit()
        await db.refresh(promo)

        logger.info(
            "[ADMIN] Promotion status updated - id=%s is_active=%s by admin=%s",
            promotion_id, payload.is_active, current_admin.id,
        )
        return PromotionResponse.model_validate(promo)
    except Exception as e:
        await db.rollback()
        logger.error("[ADMIN] Error toggling promotion: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to toggle promotion: {str(e)}")


@router.get(
    "/promotions/{promotion_id}/usages",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Lịch sử dùng khuyến mãi",
    description="Admin xem danh sách lượt dùng của một chương trình khuyến mãi.",
)
async def admin_list_promotion_usages(
    promotion_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Danh sách lượt dùng khuyến mãi.

    Args:
        promotion_id: UUID của promotion.
        page: Trang hiện tại.
        page_size: Kích thước trang.
        db: Async DB session.

    Returns:
        Dict phân trang chứa items (PromotionUsageResponse), page, page_size, total.

    Raises:
        HTTPException 404: Nếu promotion không tồn tại.
    """
    promo = await db.get(Promotion, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    base_stmt = select(PromotionUsage).where(PromotionUsage.promotion_id == promotion_id)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(PromotionUsage.used_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [PromotionUsageResponse.model_validate(u) for u in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
