"""Customer API — Wallet & Promotions (Phase 8).

Endpoints:
  GET    /customer/wallet                     Lấy ví (auto-create)
  GET    /customer/wallet/transactions        Lịch sử giao dịch (phân trang)
  POST   /customer/wallet/topup              Khởi tạo nạp tiền
  POST   /customer/promotions/validate        Validate mã giảm giá
  GET    /customer/promotions                 DS khuyến mãi khả dụng
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.payment import Promotion, Wallet, WalletTransaction
from app.models.user import User
from app.schemas.payment import (
    PromotionResponse,
    PromotionValidateRequest,
    PromotionValidateResponse,
    WalletResponse,
    WalletTopupRequest,
    WalletTopupResponse,
    WalletTransactionResponse,
)
from app.services.payment_service import PaymentService
from app.services.vnpay_service import VNPAYService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customer", tags=["Customer / Wallet & Promotions"])


# ─────────────────────────────────────────────────────────────────────
# Wallet
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/wallet",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin ví",
    description="Lấy thông tin ví của customer. Tự động tạo ví mới nếu chưa có.",
)
async def get_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> WalletResponse:
    """Lấy ví customer (auto-create nếu chưa có).

    Args:
        db: Async DB session.
        current_user: Customer đang đăng nhập.

    Returns:
        WalletResponse chứa thông tin ví.
    """
    wallet = await PaymentService.get_or_create_wallet(db, current_user.id)
    await db.commit()
    await db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


@router.get(
    "/wallet/transactions",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Lịch sử giao dịch ví",
    description="Danh sách giao dịch ví của customer, hỗ trợ phân trang và lọc theo loại.",
)
async def list_wallet_transactions(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    type: str | None = Query(None, description="Lọc theo loại giao dịch"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> dict[str, Any]:
    """Lịch sử giao dịch ví.

    Args:
        page: Số trang.
        page_size: Số item mỗi trang.
        type: Lọc theo loại giao dịch (topup/payment/refund/...).
        db: Async DB session.
        current_user: Customer đang đăng nhập.

    Returns:
        Dict phân trang chứa items (WalletTransactionResponse), page, page_size, total.
    """
    wallet = await PaymentService.get_or_create_wallet(db, current_user.id)
    await db.commit()

    base_stmt = select(WalletTransaction).where(WalletTransaction.wallet_id == wallet.id)
    if type:
        base_stmt = base_stmt.where(WalletTransaction.type == type)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(WalletTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_stmt)).scalars().all()

    return {
        "items": [WalletTransactionResponse.model_validate(t) for t in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/wallet/topup",
    response_model=WalletTopupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nạp tiền vào ví",
    description="Khởi tạo giao dịch nạp tiền. Trả về URL redirect sang cổng thanh toán (placeholder).",
)
async def topup_wallet(
    request: Request,
    payload: WalletTopupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> WalletTopupResponse:
    """Khởi tạo nạp tiền vào ví qua cổng thanh toán.

    Tạo WalletTransaction(type='topup', status='pending'). Khi gateway callback
    xác nhận thành công sẽ update status và credit balance.

    Args:
        request: FastAPI Request to extract client IP.
        payload: Thông tin nạp tiền (amount, method).
        db: Async DB session.
        current_user: Customer đang đăng nhập.

    Returns:
        WalletTopupResponse chứa transaction_id và payment_url (placeholder).
    """
    try:
        wallet = await PaymentService.get_or_create_wallet(db, current_user.id)

        txn = WalletTransaction(
            wallet_id=wallet.id,
            type="topup",
            amount=payload.amount,
            balance_after=float(wallet.balance),  # Balance chưa thay đổi cho tới callback
            description=f"Topup via {payload.method}",
            status="pending",
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        logger.info(
            "[WALLET] Topup initiated - user_id=%s amount=%s method=%s txn_id=%s",
            current_user.id, payload.amount, payload.method, txn.id,
        )

        if payload.method == "vnpay":
            # Create VNPAY real URL
            client_ip = request.client.host if request.client else "127.0.0.1"
            payment_url = VNPAYService.generate_payment_url(
                order_id=str(txn.id),
                amount=payload.amount,
                order_desc=f"Topup wallet user {current_user.id}",
                ip_addr=client_ip,
            )
        else:
            # Placeholder payment URL cho các method khác
            payment_url = f"https://sandbox.{payload.method}.vn/pay?ref={txn.id}&amount={payload.amount}"

        return WalletTopupResponse(
            transaction_id=txn.id,
            payment_url=payment_url,
            amount=payload.amount,
            method=payload.method,
        )
    except Exception as e:
        await db.rollback()
        logger.error("[WALLET] Error initiating topup: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to initiate topup: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# Promotions
# ─────────────────────────────────────────────────────────────────────

@router.post(
    "/promotions/validate",
    response_model=PromotionValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate mã giảm giá",
    description="Kiểm tra mã giảm giá có hợp lệ không và tính số tiền giảm.",
)
async def validate_promotion(
    payload: PromotionValidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> PromotionValidateResponse:
    """Validate mã giảm giá.

    Args:
        payload: Thông tin validate (code, service_type, fare).
        db: Async DB session.
        current_user: Customer đang đăng nhập.

    Returns:
        PromotionValidateResponse chứa valid, discount_amount, final_fare.
    """
    valid, promo, discount, message = await PaymentService.validate_promotion(
        db, payload.code, current_user.id, payload.service_type, payload.fare,
    )

    final_fare = max(payload.fare - discount, 0) if valid else payload.fare

    return PromotionValidateResponse(
        valid=valid,
        promotion_id=promo.id if promo else None,
        code=payload.code,
        discount_amount=discount,
        final_fare=final_fare,
        message=message,
    )


@router.get(
    "/promotions",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Danh sách khuyến mãi khả dụng",
    description="Danh sách các chương trình khuyến mãi đang có hiệu lực.",
)
async def list_available_promotions(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("customer")),
) -> dict[str, Any]:
    """Danh sách khuyến mãi đang valid.

    Args:
        page: Số trang.
        page_size: Số item mỗi trang.
        db: Async DB session.
        current_user: Customer đang đăng nhập.

    Returns:
        Dict phân trang chứa items (PromotionResponse), page, page_size, total.
    """
    now = datetime.now(tz=timezone.utc)
    base_stmt = select(Promotion).where(
        Promotion.is_active.is_(True),
        Promotion.valid_from <= now,
        Promotion.valid_to >= now,
    )

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        base_stmt
        .order_by(Promotion.valid_to.asc())
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
