"""ORM models for Phase 9.2 — Notifications & Notification Settings."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


# ─────────────────────────────────────────────────────────────────────
# Notification types (tham chiếu, không enforce ở DB level)
# booking_accepted / trip_completed / payment_received / review_received
# admin_broadcast / promotion / system / booking_updates
# ─────────────────────────────────────────────────────────────────────


class Notification(Base):
    """Thông báo in-app — lưu DB để user pull khi mở app.

    Real-time delivery qua WebSocket (Phase 11) — khi notification mới INSERT,
    Phase 11 sẽ PUBLISH lên Redis để WS Server broadcast đến client connected.
    Không dùng Firebase/FCM.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    # JSONB payload cho deep link, booking_id, review_id, etc.
    data: Mapped[dict | None] = mapped_column(JSON)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class NotificationSetting(Base):
    """Cấu hình nhận thông báo per-user per-type.

    Mặc định tất cả types đều enabled. Khi user tắt 1 type,
    notification_service sẽ skip INSERT cho type đó.
    """

    __tablename__ = "notification_settings"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "notification_type", name="uq_notification_settings_user_type"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # booking_updates / review_received / promotion / admin_broadcast / system
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])
