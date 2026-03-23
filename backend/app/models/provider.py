from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.provider_service import ProviderService
    from app.models.user import User


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'pending'")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'active'"))
    avg_rating: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default=text("0"))
    total_reviews: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_jobs_completed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    owner: Mapped[User] = relationship(
        "User",
        back_populates="owned_providers",
        foreign_keys=[owner_user_id],
    )
    individual_profile: Mapped[ProviderIndividualProfile | None] = relationship(
        back_populates="provider",
        uselist=False,
        cascade="all, delete-orphan",
    )
    business_profile: Mapped[ProviderBusinessProfile | None] = relationship(
        back_populates="provider",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents: Mapped[list[ProviderDocument]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    services: Mapped[list["ProviderService"]] = relationship(
        "ProviderService",
        back_populates="provider",
        cascade="all, delete-orphan",
    )


class ProviderIndividualProfile(Base):
    __tablename__ = "provider_individual_profiles"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    exe_year: Mapped[int | None] = mapped_column(Integer)
    cccd: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    provider: Mapped[Provider] = relationship(back_populates="individual_profile")


class ProviderBusinessProfile(Base):
    __tablename__ = "provider_business_profiles"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exe_year: Mapped[int | None] = mapped_column(Integer)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    tax_code: Mapped[str | None] = mapped_column(String(50))
    business_license_number: Mapped[str | None] = mapped_column(String(100))
    representative_name: Mapped[str | None] = mapped_column(String(255))
    representative_position: Mapped[str | None] = mapped_column(String(255))
    founded_date: Mapped[date | None] = mapped_column()
    hotline: Mapped[str | None] = mapped_column(String(20))
    website_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    provider: Mapped[Provider] = relationship(back_populates="business_profile")


class ProviderDocument(Base):
    __tablename__ = "provider_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_name: Mapped[str | None] = mapped_column(String(255))
    document_number: Mapped[str | None] = mapped_column(String(100))
    issued_by: Mapped[str | None] = mapped_column(String(255))
    issued_date: Mapped[date | None] = mapped_column()
    expiry_date: Mapped[date | None] = mapped_column()
    front_file_url: Mapped[str | None] = mapped_column(Text)
    back_file_url: Mapped[str | None] = mapped_column(Text)
    extra_file_url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'pending'")
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    provider: Mapped[Provider] = relationship(back_populates="documents")


class ProviderStatusLog(Base):
    __tablename__ = "provider_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
