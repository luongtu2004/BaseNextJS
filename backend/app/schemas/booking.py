from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────
# Pricing Engine
# ─────────────────────────────────────────────────────────────────────

class PriceConfigCreate(BaseModel):
    """Payload tạo cấu hình giá mới cho loại dịch vụ."""
    service_type: str = Field(max_length=50)
    pricing_mode: Literal["formula", "driver_quote"] = Field(default="formula")
    
    # Dùng cho formula
    base_fare: float | None = Field(default=None, ge=0)
    fare_per_km: float | None = Field(default=None, ge=0)
    fare_per_min: float | None = Field(default=None, ge=0)
    min_fare: float | None = Field(default=None, ge=0)
    surge_enabled: bool = Field(default=False)
    surge_multiplier: float | None = Field(default=1.0, ge=1.0)
    
    # Dùng cho driver_quote
    quote_timeout_sec: int | None = Field(default=120, ge=30)
    accept_timeout_sec: int | None = Field(default=60, ge=30)
    min_quote: float | None = Field(default=None, ge=0)
    max_quote: float | None = Field(default=None, ge=0)


class PriceConfigUpdate(BaseModel):
    """Payload cập nhật cấu hình giá (các trường đều tùy chọn - exclude_unset)."""
    pricing_mode: Literal["formula", "driver_quote"] | None = None
    base_fare: float | None = Field(default=None, ge=0)
    fare_per_km: float | None = Field(default=None, ge=0)
    fare_per_min: float | None = Field(default=None, ge=0)
    min_fare: float | None = Field(default=None, ge=0)
    surge_enabled: bool | None = None
    surge_multiplier: float | None = Field(default=None, ge=1.0)
    quote_timeout_sec: int | None = Field(default=None, ge=30)
    accept_timeout_sec: int | None = Field(default=None, ge=30)
    min_quote: float | None = Field(default=None, ge=0)
    max_quote: float | None = Field(default=None, ge=0)


class PriceConfigStatusPatch(BaseModel):
    """Payload để bật/tắt trạng thái hoạt động của PriceConfig."""
    is_active: bool


class PriceConfigResponse(BaseModel):
    """Response schema cho PriceConfig (bao gồm toàn bộ thông tin cấu hình giá)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_type: str
    pricing_mode: str
    base_fare: float | None
    fare_per_km: float | None
    fare_per_min: float | None
    min_fare: float | None
    surge_enabled: bool
    surge_multiplier: float | None
    quote_timeout_sec: int | None
    accept_timeout_sec: int | None
    min_quote: float | None
    max_quote: float | None
    effective_from: datetime
    effective_to: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FareEstimateRequest(BaseModel):
    """Thông tin yêu cầu ước tính cước phí."""
    service_type: str
    distance_km: float = Field(gt=0)
    duration_min: int = Field(gt=0)


class FareEstimateResponse(BaseModel):
    """Kết quả ước tính cước phí theo cấu hình hiện hành."""
    service_type: str
    pricing_mode: str
    estimated_fare: float | None = None
    min_fare: float | None = None
    max_fare: float | None = None
    currency: str = "VND"
    message: str | None = None


# ─────────────────────────────────────────────────────────────────────
# Commission Config
# ─────────────────────────────────────────────────────────────────────

class CommissionConfigCreate(BaseModel):
    """Payload tạo cấu hình hoa hồng mới cho loại dịch vụ."""
    service_type: str = Field(max_length=50)
    rate_percent: float = Field(ge=0, le=100)
    fixed_fee: float | None = Field(default=0, ge=0)


class CommissionConfigUpdate(BaseModel):
    """Payload cập nhật cấu hình hoa hồng (các trường đều tùy chọn - exclude_unset)."""
    rate_percent: float | None = Field(default=None, ge=0, le=100)
    fixed_fee: float | None = Field(default=None, ge=0)


class CommissionConfigStatusPatch(BaseModel):
    """Payload để bật/tắt trạng thái hoạt động của CommissionConfig."""
    is_active: bool


class CommissionConfigResponse(BaseModel):
    """Response schema cho CommissionConfig (bao gồm toàn bộ thông tin hoa hồng)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_type: str
    rate_percent: float
    fixed_fee: float | None
    effective_from: datetime
    effective_to: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────
# Customer Booking
# ─────────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    """Payload tạo booking mới từ phía khách hàng."""
    service_type: str
    pickup_lat: float
    pickup_lng: float
    pickup_address: str  # required — NOT NULL in DB
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    dropoff_address: str | None = None
    scheduled_time: datetime | None = None
    notes: str | None = None

class BookingResponse(BaseModel):
    """Response schema đầy đủ cho Booking (bao gồm OTP - chỉ trả cho chính khách hàng/admin)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    provider_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    service_type: str
    status: str
    pricing_mode: str
    estimated_fare: float | None = None
    final_fare: float | None = None
    distance_km: float | None = None
    duration_min: int | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    pickup_address: str | None = None
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    dropoff_address: str | None = None
    boarding_otp: str | None = None
    requested_at: datetime
    driver_quoted_at: datetime | None = None
    customer_decided_at: datetime | None = None
    accepted_at: datetime | None = None
    arrived_at: datetime | None = None
    started_at: datetime | None = None
    boarded_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BookingSummaryResponse(BaseModel):
    """Booking info for provider browse list — OTP is intentionally excluded."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    service_type: str
    status: str
    pricing_mode: str
    estimated_fare: float | None = None
    distance_km: float | None = None
    duration_min: int | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    pickup_address: str | None = None
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    dropoff_address: str | None = None
    requested_at: datetime
    notes: str | None = None


class BookingProviderResponse(BaseModel):
    """Response schema cho provider sau các thao tác accept/arrive/board/complete.

    Giống BookingResponse nhưng KHÔNG chứa boarding_otp — provider không được
    phép đọc OTP qua API (họ phải nhận từ khách hàng trực tiếp).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    provider_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    service_type: str
    status: str
    pricing_mode: str
    estimated_fare: float | None = None
    final_fare: float | None = None
    distance_km: float | None = None
    duration_min: int | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    pickup_address: str | None = None
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    dropoff_address: str | None = None
    requested_at: datetime
    accepted_at: datetime | None = None
    arrived_at: datetime | None = None
    started_at: datetime | None = None
    boarded_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────
# Provider Availability & Location
# ─────────────────────────────────────────────────────────────────────

class DriverSessionCreate(BaseModel):
    """Payload bắt đầu session online cho tài xế."""
    vehicle_id: uuid.UUID | None = None

class DriverAvailabilitySessionResponse(BaseModel):
    """Response schema cho phiên làm việc (online/offline) của tài xế."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    vehicle_id: uuid.UUID | None
    status: str
    online_at: datetime | None
    offline_at: datetime | None
    created_at: datetime

class DriverLocationUpdate(BaseModel):
    """Payload cập nhật vị trí GPS của tài xế."""
    latitude: float
    longitude: float
    heading: float | None = None
    speed_kmh: float | None = None

class DriverLocationResponse(BaseModel):
    """Response schema chứa thông tin vị trí mới nhất của tài xế."""
    model_config = ConfigDict(from_attributes=True)

    provider_id: uuid.UUID
    latitude: float
    longitude: float
    heading: float | None = None
    speed_kmh: float | None = None
    updated_at: datetime


