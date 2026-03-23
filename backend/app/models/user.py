from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.identity import UserIdentityVerification
    from app.models.provider import Provider


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    phone: Mapped[str | None] = mapped_column(String(20))
    full_name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(Text)
    gender: Mapped[int | None] = mapped_column(SmallInteger)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    dob: Mapped[date | None] = mapped_column()
    address_line: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'active'"))
    account_source: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'self_register'")
    )
    phone_verified: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    identity_verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'unverified'")
    )
    identity_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_identity_verification_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_identity_verifications.id"),
        nullable=True,
    )

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    owned_providers: Mapped[list[Provider]] = relationship(
        "Provider",
        back_populates="owner",
        foreign_keys="Provider.owner_user_id",
    )
    identity_verifications: Mapped[list[UserIdentityVerification]] = relationship(
        "UserIdentityVerification",
        back_populates="user",
        foreign_keys="UserIdentityVerification.user_id",
    )
    latest_identity_verification: Mapped[UserIdentityVerification | None] = relationship(
        "UserIdentityVerification",
        foreign_keys="User.latest_identity_verification_id",
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_code: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped[User] = relationship(back_populates="roles")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bio: Mapped[str | None] = mapped_column(Text)
    preferred_language: Mapped[str | None] = mapped_column(String(20), server_default=text("'vi'"))
    timezone: Mapped[str | None] = mapped_column(
        String(50), server_default=text("'Asia/Ho_Chi_Minh'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped[User] = relationship(back_populates="profile")


class UserStatusLog(Base):
    __tablename__ = "user_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str | None] = mapped_column(String(30))
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
