"""Provider API — Wallet & Earnings (Phase 8).

Endpoints:
  GET    /provider/wallet                     Số dư ví tài xế
  GET    /provider/wallet/transactions        Lịch sử giao dịch
  GET    /provider/me/earnings                Summary thu nhập
  GET    /provider/me/earnings/history        Chi tiết theo ngày
  POST   /provider/wallet/withdraw            Yêu cầu rút tiền
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_role
from app.db.session import get_db
from app.models.payment import Wallet, WalletTransaction
from app.models.provider import Provider
from app.models.user import User
from app.schemas.payment import (
    EarningsDailyResponse,
    EarningsSummaryResponse,
    WalletResponse,
    WalletTransactionResponse,
    WithdrawalRequest,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/provider", tags=["Provider / Wallet & Earnings"])


# ─────────────────────────────────────────────────────────────────────
# Shared Helper
# ─────────────────────────────────────────────────────────────────────

async def _get_provider_or_400(current_user: User, db: AsyncSession) -> Provider:
    """Lấy Provider profile từ user hiện tại.

    Args:
        current_user: User đang đăng nhập với role provider.
        db: Async DB session.

    Returns:
        Provider record.

    Raises:
        HTTPException 400: Nếu user chưa có profile provider.
    """
    provider = (
        await db.execute(
            select(Provider).where(Provider.owner_user_id == current_user.id)
        )
    ).scalars().first()

    if not provider:
        raise HTTPException(status_code=400, detail="Provider profile not found for user")
    return provider


# ─────────────────────────────────────────────────────────────────────
# Wallet
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/wallet",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Số dư ví tài xế",
    description="Lấy thông tin ví tài xế. Tự động tạo ví mới nếu chưa có.",
)
async def get_driver_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider_owner")),
) -> WalletResponse:
    """Lấy ví tài xế (auto-create nếu chưa có).

    Args:
        db: Async DB session.
        current_user: Provider đang đăng nhập.

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
    summary="Lịch sử giao dịch ví tài xế",
    description="Danh sách giao dịch ví tài xế, hỗ trợ phân trang và lọc theo loại.",
)
async def list_driver_transactions(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    type: str | None = Query(None, description="Lọc theo loại giao dịch"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider_owner")),
) -> dict[str, Any]:
    """Lịch sử giao dịch ví tài xế.

    Args:
        page: Số trang.
        page_size: Số item mỗi trang.
        type: Lọc theo loại giao dịch (earning/commission/withdrawal/...).
        db: Async DB session.
        current_user: Provider đang đăng nhập.

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


# ─────────────────────────────────────────────────────────────────────
# Earnings
# ─────────────────────────────────────────────────────────────────────

@router.get(
    "/me/earnings",
    response_model=EarningsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Tổng thu nhập tài xế",
    description="Tổng hợp thu nhập hôm nay, tuần này, tháng này, số chuyến và hoa hồng.",
)
async def get_earnings_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider_owner")),
) -> EarningsSummaryResponse:
    """Tổng hợp thu nhập tài xế.

    Args:
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        EarningsSummaryResponse chứa thu nhập theo period.
    """
    wallet = await PaymentService.get_or_create_wallet(db, current_user.id)
    await db.commit()

    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Single query: aggregate earnings for today/week/month + trips_today + commission_today
    from sqlalchemy import case, literal
    rows = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (WalletTransaction.type == "earning") &
                                (WalletTransaction.status == "completed") &
                                (WalletTransaction.created_at >= today_start),
                                WalletTransaction.amount,
                            ),
                            else_=literal(0),
                        )
                    ), 0,
                ).label("today_earning"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (WalletTransaction.type == "earning") &
                                (WalletTransaction.status == "completed") &
                                (WalletTransaction.created_at >= week_start),
                                WalletTransaction.amount,
                            ),
                            else_=literal(0),
                        )
                    ), 0,
                ).label("week_earning"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (WalletTransaction.type == "earning") &
                                (WalletTransaction.status == "completed") &
                                (WalletTransaction.created_at >= month_start),
                                WalletTransaction.amount,
                            ),
                            else_=literal(0),
                        )
                    ), 0,
                ).label("month_earning"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (WalletTransaction.type == "commission") &
                                (WalletTransaction.status == "completed") &
                                (WalletTransaction.created_at >= today_start),
                                func.abs(WalletTransaction.amount),
                            ),
                            else_=literal(0),
                        )
                    ), 0,
                ).label("commission_today"),
                func.count(
                    case(
                        (
                            (WalletTransaction.type == "earning") &
                            (WalletTransaction.status == "completed") &
                            (WalletTransaction.reference_type == "booking") &
                            (WalletTransaction.created_at >= today_start),
                            WalletTransaction.id,
                        ),
                        else_=None,
                    )
                ).label("trips_today"),
            ).where(
                WalletTransaction.wallet_id == wallet.id,
                WalletTransaction.created_at >= month_start,
            )
        )
    ).one()

    return EarningsSummaryResponse(
        today=float(rows.today_earning),
        this_week=float(rows.week_earning),
        this_month=float(rows.month_earning),
        total_trips_today=rows.trips_today,
        total_commission_today=float(rows.commission_today),
    )


@router.get(
    "/me/earnings/history",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Lịch sử thu nhập theo ngày",
    description="Chi tiết thu nhập tài xế theo từng ngày.",
)
async def get_earnings_history(
    days: int = Query(30, ge=1, le=90, description="Số ngày lịch sử"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider_owner")),
) -> dict[str, Any]:
    """Chi tiết thu nhập theo ngày.

    Args:
        days: Số ngày lấy lịch sử (1-90).
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        Dict chứa items (EarningsDailyResponse) sorted by date desc.
    """
    wallet = await PaymentService.get_or_create_wallet(db, current_user.id)
    await db.commit()

    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    date_col = cast(WalletTransaction.created_at, Date)

    # Earning per day
    earning_rows = (
        await db.execute(
            select(
                date_col.label("date"),
                func.coalesce(func.sum(WalletTransaction.amount), 0).label("earnings"),
                func.count().label("trips"),
            ).where(
                WalletTransaction.wallet_id == wallet.id,
                WalletTransaction.type == "earning",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= since,
            ).group_by(date_col).order_by(date_col.desc())
        )
    ).all()

    # Commission per day
    commission_rows = (
        await db.execute(
            select(
                date_col.label("date"),
                func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0).label("commission"),
            ).where(
                WalletTransaction.wallet_id == wallet.id,
                WalletTransaction.type == "commission",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= since,
            ).group_by(date_col)
        )
    ).all()

    commission_map: dict[str, float] = {
        str(row.date): float(row.commission) for row in commission_rows
    }

    items = [
        EarningsDailyResponse(
            date=str(row.date),
            earnings=float(row.earnings),
            commission=commission_map.get(str(row.date), 0),
            trips=row.trips,
        )
        for row in earning_rows
    ]

    return {
        "items": items,
        "page": 1,
        "page_size": days,
        "total": len(items),
    }


# ─────────────────────────────────────────────────────────────────────
# Withdrawal
# ─────────────────────────────────────────────────────────────────────

@router.post(
    "/wallet/withdraw",
    response_model=WalletTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yêu cầu rút tiền",
    description="Tài xế gửi yêu cầu rút tiền từ ví. Balance bị hold ngay (giống XanhSM/Grab).",
)
async def request_withdrawal(
    payload: WithdrawalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_user_role("provider_owner")),
) -> WalletTransactionResponse:
    """Tạo yêu cầu rút tiền.

    Hold balance ngay lập tức để tránh double-spend.
    Admin duyệt → chuyển khoản. Admin từ chối → hoàn lại balance.

    Args:
        payload: Thông tin rút tiền (amount, bank info).
        db: Async DB session.
        current_user: Provider đang đăng nhập.

    Returns:
        WalletTransactionResponse với status='pending'.

    Raises:
        HTTPException 400: Nếu ví frozen, thiếu tiền, hoặc đã có pending.
    """
    try:
        wallet = await PaymentService.get_or_create_wallet(db, current_user.id)

        description = f"Withdrawal to {payload.bank_name or 'N/A'} {payload.bank_account or 'N/A'}"
        txn = await PaymentService.create_withdrawal_request(db, wallet, payload.amount, description)
        await db.commit()
        await db.refresh(txn)

        logger.info("[WALLET] Provider %s requested withdrawal %s", current_user.id, payload.amount)
        return WalletTransactionResponse.model_validate(txn)
    except Exception as e:
        await db.rollback()
        logger.error("[WALLET] Error requesting withdrawal: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to request withdrawal: {str(e)}")
