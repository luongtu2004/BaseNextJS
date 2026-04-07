"""Phase 8 — Payment & Wallet: Create tables IF NOT EXISTS.

Safe for both scenarios:
  - Tables don't exist yet: will be created with all constraints.
  - Tables already exist (created via metadata.create_all): op.execute(IF NOT EXISTS) is a no-op.

Revision ID: 005b_phase8_payment
Revises: a566d875ea3b  (Phase 7)
Create Date: 2026-04-07

NOTE: This migration runs BEFORE 006_perf_indexes (which adds indexes to these tables).
The chain is: 004 -> 005b_phase8 -> 005_phase9 -> 006_perf_indexes
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "005b_phase8_payment"
# Sits between Phase 7 (a566d875ea3b) and Phase 9 (b7c91d2fe4a0)
down_revision: Union[str, Sequence[str], None] = "a566d875ea3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    """Check if a table already exists in the public schema."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = :name"
        ),
        {"name": name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # ── wallets ───────────────────────────────────────────────────────────
    if not _table_exists("wallets"):
        op.create_table(
            "wallets",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True, server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "user_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="RESTRICT"),
                nullable=False, unique=True,
            ),
            sa.Column(
                "balance", sa.Numeric(18, 2),
                nullable=False, server_default=sa.text("0"),
            ),
            sa.Column(
                "currency", sa.String(10),
                nullable=False, server_default=sa.text("'VND'"),
            ),
            sa.Column(
                "is_frozen", sa.Boolean(),
                nullable=False, server_default=sa.text("false"),
            ),
            sa.Column(
                "created_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

    # ── wallet_transactions ───────────────────────────────────────────────
    if not _table_exists("wallet_transactions"):
        op.create_table(
            "wallet_transactions",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True, server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "wallet_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("wallets.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("type", sa.String(30), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("balance_after", sa.Numeric(18, 2), nullable=False),
            sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("reference_type", sa.String(50), nullable=True),
            sa.Column("gateway_ref", sa.String(200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "status", sa.String(20),
                nullable=False, server_default=sa.text("'completed'"),
            ),
            sa.Column(
                "created_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            # Integrity: prevent double-credit on same gateway callback
            sa.UniqueConstraint(
                "gateway_ref",
                name="uq_wallet_txn_gateway_ref",
            ),
            sa.CheckConstraint(
                "type IN ('topup','payment','refund','withdrawal','earning','commission','bonus','penalty','adjust')",
                name="ck_wt_type",
            ),
        )

    # ── payment_transactions ──────────────────────────────────────────────
    if not _table_exists("payment_transactions"):
        op.create_table(
            "payment_transactions",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True, server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "booking_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("bookings.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "user_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("method", sa.String(30), nullable=False),
            sa.Column("gateway_ref", sa.String(200), nullable=True),
            sa.Column(
                "status", sa.String(20),
                nullable=False, server_default=sa.text("'pending'"),
            ),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refund_amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("metadata", postgresql.JSONB(), nullable=True),
            sa.Column(
                "created_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            # Idempotency: prevent double-processing of same gateway callback
            sa.UniqueConstraint(
                "gateway_ref",
                name="uq_pt_gateway_ref",
            ),
            sa.CheckConstraint(
                "method IN ('cash','wallet','vnpay','momo','zalopay')",
                name="ck_pt_method",
            ),
            sa.CheckConstraint(
                "status IN ('pending','completed','failed','refunded')",
                name="ck_pt_status",
            ),
        )

    # ── promotions ────────────────────────────────────────────────────────
    if not _table_exists("promotions"):
        op.create_table(
            "promotions",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True, server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("code", sa.String(50), unique=True, nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("type", sa.String(30), nullable=False),
            sa.Column("value", sa.Numeric(18, 2), nullable=False),
            sa.Column("max_discount", sa.Numeric(18, 2), nullable=True),
            sa.Column("min_fare", sa.Numeric(18, 2), nullable=True),
            sa.Column("usage_limit", sa.Integer(), nullable=True),
            sa.Column(
                "used_count", sa.Integer(),
                nullable=False, server_default=sa.text("0"),
            ),
            sa.Column(
                "per_user_limit", sa.Integer(),
                server_default=sa.text("1"), nullable=True,
            ),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
            sa.Column("service_types", postgresql.JSONB(), nullable=True),
            sa.Column(
                "is_active", sa.Boolean(),
                nullable=False, server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.CheckConstraint(
                "type IN ('percent','fixed','free_trip')",
                name="ck_promotions_type",
            ),
        )

    # ── promotion_usages ──────────────────────────────────────────────────
    if not _table_exists("promotion_usages"):
        op.create_table(
            "promotion_usages",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True, server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "promotion_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("promotions.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "user_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "booking_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("bookings.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False),
            sa.Column(
                "used_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            # Prevent double-use: 1 promo per booking
            sa.UniqueConstraint(
                "promotion_id", "booking_id",
                name="uq_promotion_booking",
            ),
        )


def downgrade() -> None:
    # Only drop if tables exist (safe if migration was partially applied)
    for table in ("promotion_usages", "promotions", "payment_transactions", "wallet_transactions", "wallets"):
        if _table_exists(table):
            op.drop_table(table)
