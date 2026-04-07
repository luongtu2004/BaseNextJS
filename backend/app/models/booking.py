from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.provider import Provider
    from app.models.taxonomy import ServiceCategory
    from app.models.transport import ProviderVehicle, ServiceRoute, ServiceRouteSchedule
    from app.models.user import User


class PriceConfig(Base):
    __tablename__ = "price_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pricing_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'formula'")
    )
    base_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    fare_per_km: Mapped[float | None] = mapped_column(Numeric(18, 2))
    fare_per_min: Mapped[float | None] = mapped_column(Numeric(18, 2))
    min_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    surge_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    surge_multiplier: Mapped[float | None] = mapped_column(Numeric(4, 2), server_default=text("1.0"))
    quote_timeout_sec: Mapped[int | None] = mapped_column(Integer, server_default=text("120"))
    accept_timeout_sec: Mapped[int | None] = mapped_column(Integer, server_default=text("60"))
    min_quote: Mapped[float | None] = mapped_column(Numeric(18, 2))
    max_quote: Mapped[float | None] = mapped_column(Numeric(18, 2))
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class CommissionConfig(Base):
    __tablename__ = "commission_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    fixed_fee: Mapped[float | None] = mapped_column(Numeric(18, 2), server_default=text("0"))
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class DriverAvailabilitySession(Base):
    __tablename__ = "driver_availability_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("provider_vehicles.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'offline'")
    )
    online_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    offline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    provider: Mapped[Provider] = relationship()
    vehicle: Mapped[ProviderVehicle | None] = relationship()


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    heading: Mapped[float | None] = mapped_column(Numeric(5, 2))
    speed_kmh: Mapped[float | None] = mapped_column(Numeric(5, 1))
    
    # PostGIS spatial column
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    provider: Mapped[Provider] = relationship()


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("providers.id", ondelete="SET NULL")
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("provider_vehicles.id", ondelete="SET NULL")
    )
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="RESTRICT"), nullable=False
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pricing_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'formula'")
    )

    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    pickup_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dropoff_address: Mapped[str | None] = mapped_column(Text)
    dropoff_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dropoff_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))

    # PostGIS spatial columns
    pickup_point = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )
    dropoff_point = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )

    route_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("service_routes.id", ondelete="SET NULL")
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("service_route_schedules.id", ondelete="SET NULL")
    )
    rental_start_date: Mapped[date | None] = mapped_column(Date)
    rental_end_date: Mapped[date | None] = mapped_column(Date)

    distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    duration_min: Mapped[int | None] = mapped_column(Integer)
    estimated_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    driver_quoted_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    quote_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    customer_accepted_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'pending'")
    )
    cancelled_by: Mapped[str | None] = mapped_column(String(20))
    cancel_reason: Mapped[str | None] = mapped_column(Text)

    boarding_otp: Mapped[str | None] = mapped_column(String(6))
    boarding_otp_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    boarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    driver_quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    customer_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    payment_method: Mapped[str | None] = mapped_column(String(30))
    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'unpaid'")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    provider: Mapped[Provider | None] = relationship(foreign_keys=[provider_id])
    vehicle: Mapped[ProviderVehicle | None] = relationship(foreign_keys=[vehicle_id])
    service_category: Mapped[ServiceCategory] = relationship(foreign_keys=[service_category_id])
    route: Mapped[ServiceRoute | None] = relationship(foreign_keys=[route_id])
    schedule: Mapped[ServiceRouteSchedule | None] = relationship(foreign_keys=[schedule_id])
    status_logs: Mapped[list[BookingStatusLog]] = relationship(
        back_populates="booking", cascade="all, delete-orphan", order_by="BookingStatusLog.created_at"
    )


class BookingStatusLog(Base):
    __tablename__ = "booking_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    booking: Mapped[Booking] = relationship(back_populates="status_logs")
    changer: Mapped[User | None] = relationship(foreign_keys=[changed_by])
