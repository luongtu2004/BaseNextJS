"""Admin Analytics API — Phase 9.3.

Endpoints:
  GET  /admin/analytics/overview    AN1 — KPI tổng quan
  GET  /admin/analytics/bookings    AN2 — Thống kê chuyến theo kỳ
  GET  /admin/analytics/revenue     AN3 — Doanh thu theo kỳ
  GET  /admin/analytics/drivers     AN4 — Top tài xế
  GET  /admin/analytics/customers   AN5 — Khách mới vs quay lại
  GET  /admin/analytics/heatmap     AN6 — Heatmap khu vực đặt xe
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import case, cast, func, select, and_, distinct, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import ColumnElement

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.booking import Booking, DriverAvailabilitySession
from app.models.payment import WalletTransaction
from app.models.provider import Provider
from app.models.review import Review
from app.models.user import User, UserRole
from app.core.constants import DEFAULT_COMMISSION_RATE
from app.schemas.analytics import (
    BookingAnalyticsResponse,
    BookingStatPoint,
    CustomerAnalyticsResponse,
    CustomerStatPoint,
    DriverAnalyticsResponse,
    DriverStatItem,
    HeatmapPoint,
    HeatmapResponse,
    OverviewResponse,
    RevenueAnalyticsResponse,
    RevenueStatPoint,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin / Analytics"])


def _date_trunc_label(period: str, col: ColumnElement) -> ColumnElement:
    """SQLAlchemy expression dể group by period.

    Args:
        period: Granularity - 'day', 'week', 'month'.
        col: SQLAlchemy column to truncate.

    Returns:
        SQLAlchemy func.to_char expression.
    """
    if period == "day":
        return func.to_char(col, "YYYY-MM-DD")
    elif period == "week":
        return func.to_char(col, "IYYY-\"W\"IW")
    else:  # month
        return func.to_char(col, "YYYY-MM")


def _validate_dates(from_date: date | None, to_date: date | None) -> tuple[date, date]:
    """Validate và normalize date range."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before or equal to to_date")
    fd = from_date or (date.today() - timedelta(days=6))
    td = to_date or date.today()
    return fd, td


# ─────────────────────────────────────────────────────────────────────
# AN1 — Overview KPI
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/overview",
    response_model=OverviewResponse,
    summary="KPI tổng quan",
    description="Dashboard overview: số chuyến hôm nay, doanh thu hôm nay, user active, tài xế online.",
)
async def admin_analytics_overview(
    period_days: int = Query(default=7, ge=1, le=90, description="Kỳ tính active users (ngày)"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> OverviewResponse:
    """KPI tổng quan nền tảng.

    Args:
        period_days: Số ngày để tính active users (mặc định 7).
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        OverviewResponse với các chỉ số KPI chính.
    """
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(date.today(), datetime.max.time()).replace(tzinfo=timezone.utc)
    active_since = datetime.combine(date.today() - timedelta(days=period_days - 1), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Parallel independent queries for performance
    (
        total_today_result,
        completed_today_result,
        pending_result,
        revenue_result,
        active_users_result,
        online_drivers_result,
        avg_rating_result,
    ) = await asyncio.gather(
        db.execute(select(func.count()).where(
            Booking.requested_at.between(today_start, today_end)
        )),
        db.execute(select(func.count()).where(
            Booking.status == "completed",
            Booking.completed_at.between(today_start, today_end),
        )),
        db.execute(select(func.count()).where(
            Booking.status.in_(["pending", "searching", "accepted", "arrived", "in_progress"])
        )),
        db.execute(select(func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0)).where(
            WalletTransaction.type == "commission",
            WalletTransaction.created_at.between(today_start, today_end),
        )),
        db.execute(select(func.count(distinct(Booking.customer_id))).where(
            Booking.requested_at >= active_since
        )),
        db.execute(select(func.count()).where(
            DriverAvailabilitySession.status == "online"
        )),
        db.execute(select(func.avg(cast(Review.rating, Float))).where(
            Review.is_visible.is_(True)
        )),
    )

    total_today = total_today_result.scalar_one()
    completed_today = completed_today_result.scalar_one()
    pending_bookings = pending_result.scalar_one()
    revenue_today = revenue_result.scalar_one()
    active_users = active_users_result.scalar_one()
    online_drivers = online_drivers_result.scalar_one()
    avg_rating = avg_rating_result.scalar_one()

    return OverviewResponse(
        total_bookings_today=total_today,
        total_completed_today=completed_today,
        total_revenue_today=float(revenue_today),
        total_active_users=active_users,
        total_online_drivers=online_drivers,
        total_pending_bookings=pending_bookings,
        avg_rating_platform=round(float(avg_rating), 2) if avg_rating else None,
        period_days=period_days,
    )


# ─────────────────────────────────────────────────────────────────────
# AN2 — Booking analytics theo kỳ
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/bookings",
    response_model=BookingAnalyticsResponse,
    summary="Thống kê chuyến theo kỳ",
    description="Tổng số chuyến, tỷ lệ hoàn thành, số hủy theo ngày/tuần/tháng.",
)
async def admin_analytics_bookings(
    from_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    period: str = Query(default="day", description="Granularity: 'day' | 'week' | 'month'"),
    service_type: str | None = Query(default=None, description="Lọc theo loại dịch vụ"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> BookingAnalyticsResponse:
    """Thống kê chuyến đi theo kỳ.

    Args:
        from_date: Ngày bắt đầu.
        to_date: Ngày kết thúc.
        period: Granularity — 'day', 'week', 'month'.
        service_type: Lọc theo loại dịch vụ.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        BookingAnalyticsResponse với list BookingStatPoint.

    Raises:
        HTTPException 400: Nếu from_date > to_date hoặc period không hợp lệ.
    """
    from_date, to_date = _validate_dates(from_date, to_date)
    if period not in ("day", "week", "month"):
        raise HTTPException(status_code=400, detail="period must be 'day', 'week', or 'month'")

    from_dt = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    period_label = _date_trunc_label(period, Booking.requested_at)

    conditions = [Booking.requested_at.between(from_dt, to_dt)]
    if service_type:
        conditions.append(Booking.service_type == service_type)

    stmt = (
        select(
            period_label.label("period"),
            func.count().label("total"),
            func.sum(case((Booking.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((Booking.status == "cancelled", 1), else_=0)).label("cancelled"),
        )
        .where(and_(*conditions))
        .group_by(period_label)
        .order_by(period_label)
    )

    rows = (await db.execute(stmt)).all()
    data = [
        BookingStatPoint(
            period=row.period,
            total_bookings=row.total,
            completed=row.completed or 0,
            cancelled=row.cancelled or 0,
            completion_rate=round((row.completed or 0) / row.total * 100, 1) if row.total else 0.0,
        )
        for row in rows
    ]

    return BookingAnalyticsResponse(
        from_date=from_date,
        to_date=to_date,
        period=period,
        data=data,
    )


# ─────────────────────────────────────────────────────────────────────
# AN3 — Revenue analytics theo kỳ
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/revenue",
    response_model=RevenueAnalyticsResponse,
    summary="Doanh thu nền tảng theo kỳ",
    description="Doanh thu hoa hồng nền tảng và tổng cước phí theo ngày/tuần/tháng.",
)
async def admin_analytics_revenue(
    from_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    period: str = Query(default="day", description="Granularity: 'day' | 'week' | 'month'"),
    service_type: str | None = Query(default=None, description="Lọc theo loại dịch vụ"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> RevenueAnalyticsResponse:
    """Doanh thu nền tảng theo kỳ.

    Args:
        from_date: Ngày bắt đầu.
        to_date: Ngày kết thúc.
        period: Granularity — 'day', 'week', 'month'.
        service_type: Lọc theo loại dịch vụ.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        RevenueAnalyticsResponse với list RevenueStatPoint.
    """
    from_date, to_date = _validate_dates(from_date, to_date)
    if period not in ("day", "week", "month"):
        raise HTTPException(status_code=400, detail="period must be 'day', 'week', or 'month'")

    from_dt = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    period_label = _date_trunc_label(period, Booking.completed_at)

    conditions = [
        Booking.status == "completed",
        Booking.completed_at.between(from_dt, to_dt),
    ]
    if service_type:
        conditions.append(Booking.service_type == service_type)

    stmt = (
        select(
            period_label.label("period"),
            func.sum(func.coalesce(Booking.final_fare, 0)).label("total_fare"),
            func.count().label("booking_count"),
        )
        .where(and_(*conditions))
        .group_by(period_label)
        .order_by(period_label)
    )

    rows = (await db.execute(stmt)).all()

    # Commission = ~15% của final_fare (heuristic — cần join wallet_transactions cho chính xác)
    data = [
        RevenueStatPoint(
            period=row.period,
            total_fare=float(row.total_fare or 0),
            platform_revenue=round(float(row.total_fare or 0) * DEFAULT_COMMISSION_RATE, 0),
            booking_count=row.booking_count,
        )
        for row in rows
    ]

    total_platform_revenue = sum(dp.platform_revenue for dp in data)

    return RevenueAnalyticsResponse(
        from_date=from_date,
        to_date=to_date,
        period=period,
        total_platform_revenue=total_platform_revenue,
        data=data,
    )


# ─────────────────────────────────────────────────────────────────────
# AN4 — Top drivers
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/drivers",
    response_model=DriverAnalyticsResponse,
    summary="Top tài xế",
    description="Danh sách tài xế xếp hạng theo số chuyến hoàn thành, rating và thu nhập.",
)
async def admin_analytics_drivers(
    from_date: date | None = Query(default=None, description="Ngày bắt đầu"),
    to_date: date | None = Query(default=None, description="Ngày kết thúc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> DriverAnalyticsResponse:
    """Thống kê tài xế — số chuyến, rating, thu nhập, tỷ lệ hủy.

    Args:
        from_date: Ngày bắt đầu lọc (optional).
        to_date: Ngày kết thúc lọc (optional).
        page: Trang hiện tại.
        page_size: Số item mỗi trang.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        DriverAnalyticsResponse với danh sách DriverStatItem và pagination.
    """
    from_date, to_date = _validate_dates(from_date, to_date)
    from_dt = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    conditions = [
        Booking.provider_id.isnot(None),
        Booking.requested_at.between(from_dt, to_dt),
    ]

    # Aggregate per provider
    subq = (
        select(
            Booking.provider_id,
            func.count().label("total_bookings"),
            func.sum(case((Booking.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((Booking.status == "cancelled", 1), else_=0)).label("cancelled"),
            func.sum(case((Booking.status == "completed", func.coalesce(Booking.final_fare, 0)), else_=0)).label("earnings"),
        )
        .where(and_(*conditions))
        .group_by(Booking.provider_id)
        .subquery()
    )

    # Rating per provider (reviewee = providers.user_id)
    rating_subq = (
        select(
            Review.reviewee_id,
            func.avg(cast(Review.rating, Float)).label("avg_rating"),
        )
        .where(Review.is_visible.is_(True), Review.reviewer_role == "customer")
        .group_by(Review.reviewee_id)
        .subquery()
    )

    total_count = (await db.execute(select(func.count()).select_from(subq))).scalar_one()

    stmt = (
        select(
            subq.c.provider_id,
            Provider.user_id,
            User.full_name,
            subq.c.completed,
            subq.c.total_bookings,
            subq.c.cancelled,
            subq.c.earnings,
            rating_subq.c.avg_rating,
        )
        .join(Provider, Provider.id == subq.c.provider_id)
        .join(User, User.id == Provider.user_id)
        .outerjoin(rating_subq, rating_subq.c.reviewee_id == Provider.user_id)
        .order_by(subq.c.completed.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = (await db.execute(stmt)).all()
    items = [
        DriverStatItem(
            provider_id=str(row.provider_id),
            full_name=row.full_name,
            total_completed=row.completed or 0,
            avg_rating=round(float(row.avg_rating), 2) if row.avg_rating else None,
            total_earnings=float(row.earnings or 0),
            cancellation_rate=round((row.cancelled or 0) / row.total_bookings * 100, 1) if row.total_bookings else 0.0,
        )
        for row in rows
    ]

    return DriverAnalyticsResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total_count,
    )


# ─────────────────────────────────────────────────────────────────────
# AN5 — Customers: new vs returning
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/customers",
    response_model=CustomerAnalyticsResponse,
    summary="Khách hàng mới vs quay lại",
    description="Thống kê số lượng khách mới và khách quay lại theo kỳ.",
)
async def admin_analytics_customers(
    from_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    period: str = Query(default="day", description="Granularity: 'day' | 'week' | 'month'"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> CustomerAnalyticsResponse:
    """Khách hàng mới (lần đầu đặt xe) vs khách quay lại theo kỳ.

    Args:
        from_date: Ngày bắt đầu.
        to_date: Ngày kết thúc.
        period: Granularity — 'day', 'week', 'month'.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        CustomerAnalyticsResponse với list CustomerStatPoint.
    """
    from_date, to_date = _validate_dates(from_date, to_date)
    if period not in ("day", "week", "month"):
        raise HTTPException(status_code=400, detail="period must be 'day', 'week', or 'month'")

    from_dt = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    to_dt = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    # Booking số thứ tự của mỗi customer — dùng ROW_NUMBER qua SQL raw
    period_label = _date_trunc_label(period, Booking.requested_at)

    # Khách hàng đặt lần đầu trong từng khoảng thời gian
    first_booking_subq = (
        select(
            Booking.customer_id,
            func.min(Booking.requested_at).label("first_booking_at"),
        )
        .group_by(Booking.customer_id)
        .subquery()
    )

    # Booking trong kỳ
    in_period = (
        select(
            Booking.customer_id,
            Booking.requested_at,
            period_label.label("period"),
            first_booking_subq.c.first_booking_at,
        )
        .join(first_booking_subq, first_booking_subq.c.customer_id == Booking.customer_id)
        .where(Booking.requested_at.between(from_dt, to_dt))
        .distinct(Booking.customer_id, period_label)
        .subquery()
    )

    stmt = (
        select(
            in_period.c.period,
            func.count(case(
                (in_period.c.first_booking_at.between(from_dt, to_dt), in_period.c.customer_id),
            )).label("new_customers"),
            func.count(case(
                (~in_period.c.first_booking_at.between(from_dt, to_dt), in_period.c.customer_id),
            )).label("returning_customers"),
        )
        .group_by(in_period.c.period)
        .order_by(in_period.c.period)
    )

    rows = (await db.execute(stmt)).all()
    data = [
        CustomerStatPoint(
            period=row.period,
            new_customers=row.new_customers or 0,
            returning_customers=row.returning_customers or 0,
        )
        for row in rows
    ]

    return CustomerAnalyticsResponse(
        from_date=from_date,
        to_date=to_date,
        period=period,
        data=data,
    )


# ─────────────────────────────────────────────────────────────────────
# AN6 — Heatmap khu vực đặt xe
# ─────────────────────────────────────────────────────────────────────


@router.get(
    "/analytics/heatmap",
    response_model=HeatmapResponse,
    summary="Heatmap khu vực đặt xe",
    description="Tổng hợp lat/lng điểm đón, làm tròn để nhóm thành các ô heatmap.",
)
async def admin_analytics_heatmap(
    from_date: date | None = Query(default=None, description="Ngày bắt đầu"),
    to_date: date | None = Query(default=None, description="Ngày kết thúc"),
    service_type: str | None = Query(default=None, description="Lọc theo loại dịch vụ"),
    precision: int = Query(default=2, ge=1, le=4, description="Số chữ số thập phân khi làm tròn tọa độ"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> HeatmapResponse:
    """Heatmap khu vực đặt xe nhiều nhất.

    Làm tròn pickup_lat/lng theo precision rồi group by để tính weight.

    Args:
        from_date: Ngày bắt đầu lọc (optional).
        to_date: Ngày kết thúc lọc (optional).
        service_type: Lọc theo loại dịch vụ (optional).
        precision: Số chữ số thập phân khi làm tròn — 2 ≈ ~1km, 3 ≈ ~100m.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        HeatmapResponse với danh sách HeatmapPoint.
    """
    conditions = [
        Booking.pickup_lat.isnot(None),
        Booking.pickup_lng.isnot(None),
    ]

    if from_date or to_date:
        from_dt_opt, to_dt_opt = _validate_dates(from_date, to_date)
        from_dt = datetime.combine(from_dt_opt, datetime.min.time()).replace(tzinfo=timezone.utc)
        to_dt_val = datetime.combine(to_dt_opt, datetime.max.time()).replace(tzinfo=timezone.utc)
        conditions.append(Booking.requested_at.between(from_dt, to_dt_val))
    if service_type:
        conditions.append(Booking.service_type == service_type)

    lat_rounded = func.round(cast(Booking.pickup_lat, Float), precision)
    lng_rounded = func.round(cast(Booking.pickup_lng, Float), precision)

    stmt = (
        select(
            lat_rounded.label("lat"),
            lng_rounded.label("lng"),
            func.count().label("weight"),
        )
        .where(and_(*conditions))
        .group_by(lat_rounded, lng_rounded)
        .order_by(func.count().desc())
        .limit(500)  # Max 500 điểm để tránh response quá lớn
    )

    rows = (await db.execute(stmt)).all()
    total = (await db.execute(select(func.count()).where(and_(*conditions)))).scalar_one()

    points = [
        HeatmapPoint(lat=float(row.lat), lng=float(row.lng), weight=row.weight)
        for row in rows
    ]

    return HeatmapResponse(
        from_date=from_date,
        to_date=to_date,
        points=points,
        total_bookings=total,
    )
