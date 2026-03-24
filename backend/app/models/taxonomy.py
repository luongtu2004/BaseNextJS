from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IndustryCategory(Base):
    __tablename__ = "industry_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str | None] = mapped_column(String(50), unique=True)
    name: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    service_categories: Mapped[list[ServiceCategory]] = relationship(
        back_populates="industry_category",
    )


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    industry_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("industry_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    industry_category: Mapped[IndustryCategory] = relationship(back_populates="service_categories")
    skills: Mapped[list[ServiceSkill]] = relationship(back_populates="service_category")
    attributes: Mapped[list[ServiceCategoryAttribute]] = relationship(
        back_populates="service_category",
        cascade="all, delete-orphan",
    )
    requirements: Mapped[list[ServiceCategoryRequirement]] = relationship(
        back_populates="service_category",
        cascade="all, delete-orphan",
    )


class ServiceSkill(Base):
    __tablename__ = "service_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    service_category: Mapped[ServiceCategory] = relationship(back_populates="skills")


class ServiceCategoryAttribute(Base):
    __tablename__ = "service_category_attributes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    attr_key: Mapped[str] = mapped_column(String(100), nullable=False)
    attr_label: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    default_value: Mapped[str | None] = mapped_column(Text)
    placeholder: Mapped[str | None] = mapped_column(Text)
    help_text: Mapped[str | None] = mapped_column(Text)
    options_json: Mapped[dict | list | None] = mapped_column(JSONB)
    validation_json: Mapped[dict | list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    service_category: Mapped[ServiceCategory] = relationship(back_populates="attributes")


class ServiceCategoryRequirement(Base):
    __tablename__ = "service_category_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement_code: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    applies_to_provider_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'all'")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    service_category: Mapped[ServiceCategory] = relationship(back_populates="requirements")
