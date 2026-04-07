"""Pydantic schemas for Phase 9.3 — Admin Analytics Dashboard."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────
# 9.3 Analytics
# ─────────────────────────────────────────────────────────────────────


class OverviewResponse(BaseModel):
    """KPI tổng quan nền tảng — dùng cho Overview card trên admin dashboard."""

    total_bookings_today: int = Field(description="Số chuyến đặt trong ngày hôm nay")
    total_completed_today: int = Field(description="Số chuyến hoàn thành hôm nay")
    total_revenue_today: float = Field(description="Doanh thu hôm nay (VNĐ)")
    total_active_users: int = Field(description="User có booking trong 7 ngày qua")
    total_online_drivers: int = Field(description="Tài xế đang online")
    total_pending_bookings: int = Field(description="Booking đang chờ xử lý")
    avg_rating_platform: float | None = Field(description="Điểm đánh giá trung bình toàn platform")
    period_days: int = Field(default=7, description="Kỳ tính active_users (ngày)")


class BookingStatPoint(BaseModel):
    """Một điểm dữ liệu trong chuỗi thời gian chuyến đi."""

    period: str = Field(description="Nhãn kỳ: '2026-04-06' (day) / '2026-W14' (week) / '2026-04' (month)")
    total_bookings: int = Field(description="Tổng số chuyến")
    completed: int = Field(description="Số chuyến hoàn thành")
    cancelled: int = Field(description="Số chuyến đã hủy")
    completion_rate: float = Field(description="Tỷ lệ hoàn thành (%)")


class BookingAnalyticsResponse(BaseModel):
    """Thống kê chuyến đi theo kỳ."""

    from_date: date = Field(description="Ngày bắt đầu")
    to_date: date = Field(description="Ngày kết thúc")
    period: str = Field(description="Granularity: 'day' | 'week' | 'month'")
    data: list[BookingStatPoint] = Field(description="Chuỗi dữ liệu theo kỳ")


class RevenueStatPoint(BaseModel):
    """Một điểm dữ liệu doanh thu theo kỳ."""

    period: str = Field(description="Nhãn kỳ")
    platform_revenue: float = Field(description="Hoa hồng nền tảng thu được (VNĐ)")
    total_fare: float = Field(description="Tổng giá trị cước phí (VNĐ)")
    booking_count: int = Field(description="Số chuyến hoàn thành trong kỳ")


class RevenueAnalyticsResponse(BaseModel):
    """Doanh thu nền tảng theo kỳ."""

    from_date: date = Field(description="Ngày bắt đầu")
    to_date: date = Field(description="Ngày kết thúc")
    period: str = Field(description="Granularity: 'day' | 'week' | 'month'")
    total_platform_revenue: float = Field(description="Tổng doanh thu cả kỳ (VNĐ)")
    data: list[RevenueStatPoint] = Field(description="Chuỗi dữ liệu theo kỳ")


class DriverStatItem(BaseModel):
    """Thống kê một tài xế — dùng cho bảng Top Drivers."""

    provider_id: str = Field(description="UUID provider")
    full_name: str | None = Field(description="Tên tài xế")
    total_completed: int = Field(description="Tổng chuyến hoàn thành")
    avg_rating: float | None = Field(description="Điểm đánh giá trung bình")
    total_earnings: float = Field(description="Tổng thu nhập (VNĐ)")
    cancellation_rate: float = Field(description="Tỷ lệ hủy chuyến (%)")


class DriverAnalyticsResponse(BaseModel):
    """Danh sách top tài xế."""

    items: list[DriverStatItem] = Field(description="Danh sách tài xế")
    page: int = Field(description="Trang hiện tại")
    page_size: int = Field(description="Số item mỗi trang")
    total: int = Field(description="Tổng số tài xế có chuyến")


class CustomerStatPoint(BaseModel):
    """Thống kê khách hàng mới vs quay lại theo kỳ."""

    period: str = Field(description="Nhãn kỳ")
    new_customers: int = Field(description="Khách mới (lần đầu đặt xe)")
    returning_customers: int = Field(description="Khách quay lại (đã đặt trước đó)")


class CustomerAnalyticsResponse(BaseModel):
    """Khách hàng mới vs quay lại theo kỳ."""

    from_date: date = Field(description="Ngày bắt đầu")
    to_date: date = Field(description="Ngày kết thúc")
    period: str = Field(description="Granularity: 'day' | 'week' | 'month'")
    data: list[CustomerStatPoint] = Field(description="Chuỗi dữ liệu theo kỳ")


class HeatmapPoint(BaseModel):
    """Một điểm toạ độ cho heatmap đặt xe."""

    lat: float = Field(description="Vĩ độ")
    lng: float = Field(description="Kinh độ")
    weight: int = Field(description="Số lần đặt xe tại khu vực này")


class HeatmapResponse(BaseModel):
    """Heatmap khu vực đặt xe nhiều nhất."""

    from_date: date | None = Field(description="Ngày bắt đầu lọc")
    to_date: date | None = Field(description="Ngày kết thúc lọc")
    points: list[HeatmapPoint] = Field(description="Danh sách điểm toạ độ + trọng số")
    total_bookings: int = Field(description="Tổng số booking trong kỳ")
