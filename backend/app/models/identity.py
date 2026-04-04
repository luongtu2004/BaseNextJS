from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class UserIdentityVerification(Base):
    __tablename__ = "user_identity_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    verification_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'cccd'")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'draft'"))
    review_mode: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'hybrid'")
    )
    full_name_on_id: Mapped[str | None] = mapped_column(String(255))
    date_of_birth_on_id: Mapped[date | None] = mapped_column()
    gender_on_id: Mapped[int | None] = mapped_column(SmallInteger)
    id_number: Mapped[str | None] = mapped_column(String(50))
    nationality: Mapped[str | None] = mapped_column(String(100))
    place_of_origin: Mapped[str | None] = mapped_column(Text)
    place_of_residence: Mapped[str | None] = mapped_column(Text)
    issue_date: Mapped[date | None] = mapped_column()
    expiry_date: Mapped[date | None] = mapped_column()
    issuing_authority: Mapped[str | None] = mapped_column(String(255))
    extracted_address: Mapped[str | None] = mapped_column(Text)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    face_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    liveness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="identity_verifications",
        foreign_keys=[user_id],
    )


class UserIdentityFile(Base):
    __tablename__ = "user_identity_files"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_identity_verifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    storage_provider: Mapped[str | None] = mapped_column(String(50))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(128))
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class UserIdentityVerificationLog(Base):
    __tablename__ = "user_identity_verification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_identity_verifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(100))
    request_payload_json: Mapped[dict | list | None] = mapped_column(JSONB)
    response_payload_json: Mapped[dict | list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class UserIdentityReviewDecision(Base):
    __tablename__ = "user_identity_review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_identity_verifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
