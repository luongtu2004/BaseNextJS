"""Pydantic schemas for Phase 6 — Transport & Logistics.

Covers: ProviderVehicle, ProviderVehicleDocument,
        ServiceRoute, ServiceRouteSchedule,
        ProviderVehicleAvailability.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


# ─────────────────────────────────────────────────────────────────────
# Provider Vehicle
# ─────────────────────────────────────────────────────────────────────

class ProviderVehicleCreate(BaseModel):
    """Payload để provider thêm xe mới."""

    vehicle_type: str = Field(
        min_length=1, max_length=50,
        description="Loại xe: xe_may, xe_4_cho, xe_7_cho, xe_tai, v.v.",
    )
    vehicle_brand: str | None = Field(default=None, max_length=100, description="Hãng xe")
    vehicle_model: str | None = Field(default=None, max_length=100, description="Dòng xe")
    year_of_manufacture: int | None = Field(
        default=None, ge=1900, le=2030, description="Năm sản xuất"
    )
    license_plate: str | None = Field(
        default=None, max_length=20, description="Biển số xe"
    )
    seat_count: int | None = Field(default=None, ge=1, le=100, description="Số chỗ ngồi")
    fuel_type: str | None = Field(
        default=None, max_length=20, description="Nhiên liệu: xang, dau, dien, hybrid"
    )
    transmission: str | None = Field(
        default=None, max_length=20, description="Hộp số: auto, manual"
    )
    has_ac: bool = Field(default=False, description="Có điều hòa không")
    has_wifi: bool = Field(default=False, description="Có WiFi không")
    color: str | None = Field(default=None, max_length=50, description="Màu xe")
    notes: str | None = Field(default=None, description="Ghi chú thêm")
    service_id: uuid.UUID | None = Field(
        default=None, description="Gắn xe với dịch vụ cụ thể của provider"
    )


class ProviderVehicleUpdate(BaseModel):
    """Payload để provider cập nhật thông tin xe.

    Tất cả trường đều optional — chỉ trường được gửi mới được update.
    """

    vehicle_type: str | None = Field(default=None, max_length=50)
    vehicle_brand: str | None = Field(default=None, max_length=100)
    vehicle_model: str | None = Field(default=None, max_length=100)
    year_of_manufacture: int | None = Field(default=None, ge=1900, le=2030)
    license_plate: str | None = Field(default=None, max_length=20)
    seat_count: int | None = Field(default=None, ge=1, le=100)
    fuel_type: str | None = Field(default=None, max_length=20)
    transmission: str | None = Field(default=None, max_length=20)
    has_ac: bool | None = None
    has_wifi: bool | None = None
    color: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    service_id: uuid.UUID | None = None


class VehicleStatusPatch(BaseModel):
    """Thay đổi trạng thái xe: active | inactive (dùng cho provider)."""

    status: Literal["active", "inactive"] = Field(description="Trạng thái mới: active hoặc inactive")


class AdminVehicleStatusPatch(BaseModel):
    """Thay đổi trạng thái xe: active | inactive | suspended (dùng cho admin)."""

    status: Literal["active", "inactive", "suspended"] = Field(
        description="Trạng thái mới: active, inactive hoặc suspended"
    )


class ProviderVehicleResponse(BaseModel):
    """Thông tin xe trả về cho provider và admin."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    service_id: uuid.UUID | None
    vehicle_type: str
    vehicle_brand: str | None
    vehicle_model: str | None
    year_of_manufacture: int | None
    license_plate: str | None
    seat_count: int | None
    fuel_type: str | None
    transmission: str | None
    has_ac: bool
    has_wifi: bool
    color: str | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────
# Provider Vehicle Document
# ─────────────────────────────────────────────────────────────────────

class VehicleDocumentCreate(BaseModel):
    """Payload để thêm giấy tờ xe."""

    document_type: str = Field(
        min_length=1, max_length=50,
        description="Loại giấy tờ: dang_ky_xe, dang_kiem_xe, bao_hiem_tnds, v.v.",
    )
    document_number: str | None = Field(default=None, max_length=100, description="Số hiệu giấy tờ")
    issued_date: date | None = Field(default=None, description="Ngày cấp")
    expiry_date: date | None = Field(default=None, description="Ngày hết hạn")
    file_url: str | None = Field(default=None, description="URL file ảnh/PDF đã upload")


class VehicleDocumentUpdate(BaseModel):
    """Payload để cập nhật giấy tờ xe."""

    document_number: str | None = Field(default=None, max_length=100)
    issued_date: date | None = None
    expiry_date: date | None = None
    file_url: str | None = None


class VehicleDocumentResponse(BaseModel):
    """Giấy tờ xe trả về cho provider và admin."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    document_type: str
    document_number: str | None
    issued_date: date | None
    expiry_date: date | None
    file_url: str | None
    review_status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime


class VehicleDocumentReviewRequest(BaseModel):
    """Admin duyệt hoặc từ chối giấy tờ xe."""

    action: Literal["approved", "rejected"] = Field(description="approved hoặc rejected")
    note: str | None = Field(default=None, description="Lý do từ chối (bắt buộc khi rejected)")


# ─────────────────────────────────────────────────────────────────────
# Service Route
# ─────────────────────────────────────────────────────────────────────

class ServiceRouteCreate(BaseModel):
    """Payload để provider tạo tuyến đường mới."""

    from_province: str = Field(
        min_length=1, max_length=100, description="Tỉnh/TP khởi hành"
    )
    to_province: str = Field(
        min_length=1, max_length=100, description="Tỉnh/TP đến"
    )
    distance_km: float | None = Field(default=None, ge=0, description="Khoảng cách (km)")
    duration_min: int | None = Field(default=None, ge=0, description="Thời gian ước tính (phút)")
    price: float = Field(gt=0, description="Giá vé (VNĐ)")
    notes: str | None = Field(default=None, description="Ghi chú")


class ServiceRouteUpdate(BaseModel):
    """Payload để provider cập nhật tuyến đường."""

    from_province: str | None = Field(default=None, max_length=100)
    to_province: str | None = Field(default=None, max_length=100)
    distance_km: float | None = Field(default=None, ge=0)
    duration_min: int | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, gt=0)
    notes: str | None = None


class RouteStatusPatch(BaseModel):
    """Bật / tắt tuyến đường."""

    is_active: bool = Field(description="true = bật, false = tắt")


class ServiceRouteScheduleItem(BaseModel):
    """Lịch khởi hành trong response của route."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    departure_time: time
    seat_count: int
    is_active: bool
    notes: str | None


class ServiceRouteResponse(BaseModel):
    """Tuyến đường trả về cho provider / customer / admin."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_service_id: uuid.UUID
    from_province: str
    to_province: str
    distance_km: float | None
    duration_min: int | None
    price: float
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    schedules: list[ServiceRouteScheduleItem] = []


# ─────────────────────────────────────────────────────────────────────
# Service Route Schedule
# ─────────────────────────────────────────────────────────────────────

class ServiceRouteScheduleCreate(BaseModel):
    """Payload để thêm lịch khởi hành vào tuyến."""

    departure_time: time = Field(description="Giờ khởi hành (HH:MM)")
    seat_count: int = Field(gt=0, description="Số ghế / chuyến")
    notes: str | None = Field(default=None)


class ServiceRouteScheduleUpdate(BaseModel):
    """Payload để cập nhật lịch khởi hành."""

    departure_time: time | None = None
    seat_count: int | None = Field(default=None, gt=0)
    notes: str | None = None


class ScheduleStatusPatch(BaseModel):
    """Bật / tắt một lịch cụ thể."""

    is_active: bool


class ServiceRouteScheduleResponse(BaseModel):
    """Lịch khởi hành trả về."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_id: uuid.UUID
    departure_time: time
    seat_count: int
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────
# Vehicle Availability
# ─────────────────────────────────────────────────────────────────────

class AvailabilityBlockRequest(BaseModel):
    """Payload để provider block các ngày không cho thuê."""

    dates: list[date] = Field(min_length=1, description="Danh sách ngày cần block")
    reason: str | None = Field(default=None, description="Lý do block")


class AvailabilityUnblockRequest(BaseModel):
    """Payload để provider mở lại các ngày đã block."""

    dates: list[date] = Field(min_length=1, description="Danh sách ngày cần unblock")


class AvailabilityItem(BaseModel):
    """Một ngày trong lịch availability."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date
    is_blocked: bool
    blocked_reason: str | None


class VehicleAvailabilityResponse(BaseModel):
    """Lịch availability của một xe trong khoảng thời gian."""

    vehicle_id: uuid.UUID
    items: list[AvailabilityItem]


# ─────────────────────────────────────────────────────────────────────
# Customer-facing schemas
# ─────────────────────────────────────────────────────────────────────

class CustomerTransportSearchItem(BaseModel):
    """Kết quả tìm kiếm dịch vụ vận tải cho khách."""

    model_config = ConfigDict(from_attributes=True)

    provider_id: uuid.UUID
    service_id: uuid.UUID
    service_category_code: str
    service_category_name: str
    provider_name: str
    verification_status: str
    avg_rating: float
    total_reviews: int


class CustomerRouteSearchItem(BaseModel):
    """Tuyến xe khách tìm thấy theo from/to."""

    id: uuid.UUID
    provider_service_id: uuid.UUID
    from_province: str
    to_province: str
    price: float
    duration_min: int | None
    active_schedule_count: int


class CustomerRentalVehicleItem(BaseModel):
    """Xe cho thuê tự lái trong kết quả tìm kiếm."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    vehicle_type: str
    vehicle_brand: str | None
    vehicle_model: str | None
    year_of_manufacture: int | None
    seat_count: int | None
    fuel_type: str | None
    transmission: str | None
    has_ac: bool
    status: str


class CustomerRouteScheduleItem(BaseModel):
    """Lịch khởi hành rút gọn trong chi tiết tuyến cho customer."""

    id: uuid.UUID
    departure_time: str = Field(description="Giờ khởi hành dạng HH:MM:SS")
    seat_count: int


class CustomerRouteDetailResponse(BaseModel):
    """Chi tiết tuyến đường kèm lịch khởi hành đang hoạt động — dành cho customer."""

    id: uuid.UUID
    provider_service_id: uuid.UUID
    from_province: str
    to_province: str
    distance_km: float | None
    duration_min: int | None
    price: float
    notes: str | None
    schedules: list[CustomerRouteScheduleItem]
