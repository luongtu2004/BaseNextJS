from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.provider import Provider


class ProviderService(Base):
    __tablename__ = "provider_services"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    industry_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("industry_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("service_skills.id", ondelete="RESTRICT"),
    )
    exe_year: Mapped[int | None] = mapped_column(Integer)
    pricing_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'negotiable'")
    )
    base_price: Mapped[float | None] = mapped_column(Numeric(18, 2))
    price_unit: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'pending'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    provider: Mapped["Provider"] = relationship("Provider", back_populates="services")
    attributes: Mapped[list[ProviderServiceAttribute]] = relationship(
        back_populates="provider_service",
        cascade="all, delete-orphan",
    )


class ProviderServiceAttribute(Base):
    __tablename__ = "provider_service_attributes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider_service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_services.id", ondelete="CASCADE"),
        nullable=False,
    )
    attr_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[float | None] = mapped_column(Numeric(18, 2))
    value_boolean: Mapped[bool | None] = mapped_column()
    value_json: Mapped[dict | list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    provider_service: Mapped[ProviderService] = relationship(back_populates="attributes")


class ProviderDocumentService(Base):
    __tablename__ = "provider_document_services"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_services.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
