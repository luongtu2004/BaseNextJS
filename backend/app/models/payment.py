from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


# ─────────────────────────────────────────────────────────────────────
# 8.1  Wallets
# ─────────────────────────────────────────────────────────────────────

class Wallet(Base):
    """Ví điện tử — mỗi user (customer hoặc driver) có 1 ví duy nhất."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    balance: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, server_default=text("0"),
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'VND'"),
    )
    is_frozen: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    transactions: Mapped[list[WalletTransaction]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="WalletTransaction.created_at.desc()",
    )


class WalletTransaction(Base):
    """Giao dịch ví — immutable ledger. amount > 0 = credit, < 0 = debit."""

    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="RESTRICT"), nullable=False,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    reference_type: Mapped[str | None] = mapped_column(String(50))
    gateway_ref: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'completed'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    wallet: Mapped[Wallet] = relationship(back_populates="transactions")


# ─────────────────────────────────────────────────────────────────────
# 8.2  Payment Transactions (cổng thanh toán)
# ─────────────────────────────────────────────────────────────────────

class PaymentTransaction(Base):
    """Giao dịch thanh toán qua cổng (VNPay/MoMo/ZaloPay) hoặc tiền mặt."""

    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    gateway_ref: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'"),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refund_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # "metadata" is reserved by SQLAlchemy Base — use column name alias
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    booking: Mapped[Booking] = relationship(foreign_keys=[booking_id])
    user: Mapped[User] = relationship(foreign_keys=[user_id])


# ─────────────────────────────────────────────────────────────────────
# 8.3  Promotions
# ─────────────────────────────────────────────────────────────────────

class Promotion(Base):
    """Chương trình khuyến mãi / mã giảm giá do admin tạo."""

    __tablename__ = "promotions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    max_discount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    min_fare: Mapped[float | None] = mapped_column(Numeric(18, 2))
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    per_user_limit: Mapped[int | None] = mapped_column(Integer, server_default=text("1"))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_types: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    usages: Mapped[list[PromotionUsage]] = relationship(
        back_populates="promotion", cascade="all, delete-orphan",
    )


class PromotionUsage(Base):
    """Ghi nhận mỗi lần user dùng mã giảm giá cho 1 booking."""

    __tablename__ = "promotion_usages"
    __table_args__ = (
        UniqueConstraint("promotion_id", "booking_id", name="uq_promotion_booking"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    promotion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promotions.id", ondelete="RESTRICT"), nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False,
    )
    discount_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    promotion: Mapped[Promotion] = relationship(back_populates="usages")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    booking: Mapped[Booking] = relationship(foreign_keys=[booking_id])
