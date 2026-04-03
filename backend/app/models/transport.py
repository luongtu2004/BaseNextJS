"""ORM models for Phase 6 — Transport & Logistics.

Tables: provider_vehicles, provider_vehicle_documents,
        service_routes, service_route_schedules,
        provider_vehicle_availabilities.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.provider import Provider
    from app.models.provider_service import ProviderService


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ProviderVehicle(Base):
    """Phương tiện do provider khai báo.

    Dùng cho các dịch vụ: cho thuê xe tự lái, xe tải hợp đồng,
    xe khách liên tỉnh, cứu hộ, v.v.
    """

    __tablename__ = "provider_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("provider_services.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_brand: Mapped[str | None] = mapped_column(String(100))
    vehicle_model: Mapped[str | None] = mapped_column(String(100))
    year_of_manufacture: Mapped[int | None] = mapped_column(Integer)
    license_plate: Mapped[str | None] = mapped_column(String(20))
    seat_count: Mapped[int | None] = mapped_column(Integer)
    fuel_type: Mapped[str | None] = mapped_column(String(20))
    transmission: Mapped[str | None] = mapped_column(String(20))
    has_ac: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    color: Mapped[str | None] = mapped_column(String(50))
    # active | inactive | suspended
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default=text("'active'"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    provider: Mapped["Provider"] = relationship("Provider", back_populates="vehicles")
    documents: Mapped[list[ProviderVehicleDocument]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    availabilities: Mapped[list[ProviderVehicleAvailability]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class ProviderVehicleDocument(Base):
    """Giấy tờ pháp lý của từng xe: đăng kiểm, bảo hiểm, đăng ký."""

    __tablename__ = "provider_vehicle_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_vehicles.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100))
    issued_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    file_url: Mapped[str | None] = mapped_column(Text)
    # pending | approved | rejected
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default=text("'pending'")
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    vehicle: Mapped[ProviderVehicle] = relationship(back_populates="documents")


class ServiceRoute(Base):
    """Tuyến đường cố định dành cho xe khách liên tỉnh, xe ghép, limousine."""

    __tablename__ = "service_routes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    provider_service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_services.id", ondelete="CASCADE"), nullable=False
    )
    from_province: Mapped[str] = mapped_column(String(100), nullable=False)
    to_province: Mapped[str] = mapped_column(String(100), nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    duration_min: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )

    schedules: Mapped[list[ServiceRouteSchedule]] = relationship(
        back_populates="route", cascade="all, delete-orphan"
    )


class ServiceRouteSchedule(Base):
    """Lịch khởi hành cụ thể cho một tuyến đường."""

    __tablename__ = "service_route_schedules"

    __table_args__ = (
        UniqueConstraint("route_id", "departure_time", name="uq_schedule_route_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_routes.id", ondelete="CASCADE"), nullable=False
    )
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    seat_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("now()")
    )

    route: Mapped[ServiceRoute] = relationship(back_populates="schedules")


class ProviderVehicleAvailability(Base):
    """Lịch block / unblock xe cho thuê theo ngày.

    is_blocked=True nghĩa là xe KHÔNG cho thuê ngày đó.
    Chỉ lưu các ngày bị block; ngày không có record = xe rảnh.
    """

    __tablename__ = "provider_vehicle_availabilities"

    __table_args__ = (
        UniqueConstraint("vehicle_id", "date", name="uq_vehicle_availability_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_vehicles.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    blocked_reason: Mapped[str | None] = mapped_column(Text)

    vehicle: Mapped[ProviderVehicle] = relationship(back_populates="availabilities")
