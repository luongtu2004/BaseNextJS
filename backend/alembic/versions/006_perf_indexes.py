"""Phase 6-7-8-9 Performance Indexes — add missing DB indexes.

Context: Tables already exist (created via metadata.create_all or prior migrations).
This migration ONLY adds indexes for production-scale performance.
Target: support millions of bookings, wallet transactions, notifications.

Revision ID: 006_perf_indexes
Revises: b7c91d2fe4a0 (Phase 9)
Create Date: 2026-04-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers
revision: str = "006_perf_indexes"
down_revision: Union[str, Sequence[str], None] = "b7c91d2fe4a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(name: str) -> bool:
    """Check if an index already exists (safe guard for idempotent runs)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
        {"name": name},
    )
    return result.fetchone() is not None


def _create_if_not_exists(name: str, create_fn) -> None:
    """Create index only if it does not already exist."""
    if not _index_exists(name):
        create_fn()


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────
    # Phase 7 — bookings (CRITICAL: was 0 indexes)
    # ─────────────────────────────────────────────────────────────────

    # Hot query 1: Customer xem lịch sử chuyến — WHERE customer_id = ? ORDER BY requested_at DESC
    _create_if_not_exists(
        "ix_bookings_customer_requested",
        lambda: op.create_index(
            "ix_bookings_customer_requested",
            "bookings",
            ["customer_id", sa.text("requested_at DESC")],
        ),
    )

    # Hot query 2: Provider xem chuyến của mình — WHERE provider_id = ? AND status = ?
    _create_if_not_exists(
        "ix_bookings_provider_status",
        lambda: op.create_index(
            "ix_bookings_provider_status",
            "bookings",
            ["provider_id", "status"],
        ),
    )

    # Hot query 3: Tài xế duyệt cuốc chờ — WHERE status = 'pending' ORDER BY requested_at
    # Partial index: chỉ index pending rows (< 1% tổng data, cực nhỏ + cực nhanh)
    _create_if_not_exists(
        "ix_bookings_pending_partial",
        lambda: op.create_index(
            "ix_bookings_pending_partial",
            "bookings",
            [sa.text("requested_at DESC")],
            postgresql_where=sa.text("status = 'pending'"),
        ),
    )

    # Hot query 4: Admin analytics — status + time range scans
    _create_if_not_exists(
        "ix_bookings_status_requested",
        lambda: op.create_index(
            "ix_bookings_status_requested",
            "bookings",
            ["status", sa.text("requested_at DESC")],
        ),
    )

    # Hot query 5: Revenue analytics — completed_at range scans
    _create_if_not_exists(
        "ix_bookings_completed_at",
        lambda: op.create_index(
            "ix_bookings_completed_at",
            "bookings",
            [sa.text("completed_at DESC")],
            postgresql_where=sa.text("completed_at IS NOT NULL"),
        ),
    )

    # Hot query 6: Heatmap analytics — pickup_lat/lng WHERE NOT NULL
    _create_if_not_exists(
        "ix_bookings_pickup_coords",
        lambda: op.create_index(
            "ix_bookings_pickup_coords",
            "bookings",
            ["pickup_lat", "pickup_lng"],
            postgresql_where=sa.text("pickup_lat IS NOT NULL AND pickup_lng IS NOT NULL"),
        ),
    )

    # Hot query 7: Payment service — lookup by customer + payment_status
    _create_if_not_exists(
        "ix_bookings_customer_payment",
        lambda: op.create_index(
            "ix_bookings_customer_payment",
            "bookings",
            ["customer_id", "payment_status"],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 7 — booking_status_logs
    # ─────────────────────────────────────────────────────────────────

    _create_if_not_exists(
        "ix_bsl_booking_created",
        lambda: op.create_index(
            "ix_bsl_booking_created",
            "booking_status_logs",
            ["booking_id", sa.text("created_at ASC")],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 7 — driver_availability_sessions
    # ─────────────────────────────────────────────────────────────────

    # Online/offline lookup per provider
    _create_if_not_exists(
        "ix_das_provider_status",
        lambda: op.create_index(
            "ix_das_provider_status",
            "driver_availability_sessions",
            ["provider_id", "status"],
        ),
    )

    # Count all online drivers (analytics)
    _create_if_not_exists(
        "ix_das_status_online_partial",
        lambda: op.create_index(
            "ix_das_status_online_partial",
            "driver_availability_sessions",
            ["provider_id"],
            postgresql_where=sa.text("status = 'online'"),
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 8 — wallets
    # ─────────────────────────────────────────────────────────────────

    # user_id lookup (unique = already an index but let's be explicit)
    _create_if_not_exists(
        "ix_wallets_user_id",
        lambda: op.create_index(
            "ix_wallets_user_id",
            "wallets",
            ["user_id"],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 8 — wallet_transactions
    # ─────────────────────────────────────────────────────────────────

    # Hot: lịch sử giao dịch ví — WHERE wallet_id = ? ORDER BY created_at DESC
    _create_if_not_exists(
        "ix_wt_wallet_created",
        lambda: op.create_index(
            "ix_wt_wallet_created",
            "wallet_transactions",
            ["wallet_id", sa.text("created_at DESC")],
        ),
    )

    # Hot: filter by type (earning/commission/withdrawal) cho earnings analytics
    _create_if_not_exists(
        "ix_wt_wallet_type_created",
        lambda: op.create_index(
            "ix_wt_wallet_type_created",
            "wallet_transactions",
            ["wallet_id", "type", sa.text("created_at DESC")],
        ),
    )

    # Hot: dispute/audit — lookup by reference_id (booking_id, payment_id)
    _create_if_not_exists(
        "ix_wt_reference",
        lambda: op.create_index(
            "ix_wt_reference",
            "wallet_transactions",
            ["reference_id"],
            postgresql_where=sa.text("reference_id IS NOT NULL"),
        ),
    )

    # Revenue analytics — commission transactions by date
    _create_if_not_exists(
        "ix_wt_type_created",
        lambda: op.create_index(
            "ix_wt_type_created",
            "wallet_transactions",
            ["type", sa.text("created_at DESC")],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 8 — payment_transactions
    # ─────────────────────────────────────────────────────────────────

    # Hot: lookup payment by booking
    _create_if_not_exists(
        "ix_pt_booking",
        lambda: op.create_index(
            "ix_pt_booking",
            "payment_transactions",
            ["booking_id"],
        ),
    )

    # Hot: user payment history
    _create_if_not_exists(
        "ix_pt_user_created",
        lambda: op.create_index(
            "ix_pt_user_created",
            "payment_transactions",
            ["user_id", sa.text("created_at DESC")],
        ),
    )

    # Partial: pending payments (webhook lookup)
    _create_if_not_exists(
        "ix_pt_pending_partial",
        lambda: op.create_index(
            "ix_pt_pending_partial",
            "payment_transactions",
            ["gateway_ref"],
            postgresql_where=sa.text("status = 'pending'"),
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 8 — promotions + promotion_usages
    # ─────────────────────────────────────────────────────────────────

    # Active promotions lookup (code already unique-indexed)
    _create_if_not_exists(
        "ix_promotions_active",
        lambda: op.create_index(
            "ix_promotions_active",
            "promotions",
            ["is_active", "valid_from", "valid_to"],
            postgresql_where=sa.text("is_active = true"),
        ),
    )

    # Per-user promo usage check (for per_user_limit validation)
    _create_if_not_exists(
        "ix_pu_user_promotion",
        lambda: op.create_index(
            "ix_pu_user_promotion",
            "promotion_usages",
            ["user_id", "promotion_id"],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 9 — reviews (complement existing indexes)
    # ─────────────────────────────────────────────────────────────────

    # reviewer_id lookup (customer xem reviews họ đã viết)
    _create_if_not_exists(
        "ix_reviews_reviewer",
        lambda: op.create_index(
            "ix_reviews_reviewer",
            "reviews",
            ["reviewer_id", sa.text("created_at DESC")],
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 9 — notification_settings (complement UNIQUE index)
    # ─────────────────────────────────────────────────────────────────

    # Batch disabled fetch (used in bulk_create_notifications)
    _create_if_not_exists(
        "ix_ns_user_type_disabled",
        lambda: op.create_index(
            "ix_ns_user_type_disabled",
            "notification_settings",
            ["notification_type", "user_id"],
            postgresql_where=sa.text("is_enabled = false"),
        ),
    )


def downgrade() -> None:
    # Reviews
    op.drop_index("ix_reviews_reviewer", table_name="reviews")
    op.drop_index("ix_ns_user_type_disabled", table_name="notification_settings")

    # Promotions
    op.drop_index("ix_pu_user_promotion", table_name="promotion_usages")
    op.drop_index("ix_promotions_active", table_name="promotions")

    # Payment transactions
    op.drop_index("ix_pt_pending_partial", table_name="payment_transactions")
    op.drop_index("ix_pt_user_created", table_name="payment_transactions")
    op.drop_index("ix_pt_booking", table_name="payment_transactions")

    # Wallet transactions
    op.drop_index("ix_wt_type_created", table_name="wallet_transactions")
    op.drop_index("ix_wt_reference", table_name="wallet_transactions")
    op.drop_index("ix_wt_wallet_type_created", table_name="wallet_transactions")
    op.drop_index("ix_wt_wallet_created", table_name="wallet_transactions")

    # Wallets
    op.drop_index("ix_wallets_user_id", table_name="wallets")

    # Driver sessions
    op.drop_index("ix_das_status_online_partial", table_name="driver_availability_sessions")
    op.drop_index("ix_das_provider_status", table_name="driver_availability_sessions")

    # Booking status logs
    op.drop_index("ix_bsl_booking_created", table_name="booking_status_logs")

    # Bookings
    op.drop_index("ix_bookings_customer_payment", table_name="bookings")
    op.drop_index("ix_bookings_pickup_coords", table_name="bookings")
    op.drop_index("ix_bookings_completed_at", table_name="bookings")
    op.drop_index("ix_bookings_status_requested", table_name="bookings")
    op.drop_index("ix_bookings_pending_partial", table_name="bookings")
    op.drop_index("ix_bookings_provider_status", table_name="bookings")
    op.drop_index("ix_bookings_customer_requested", table_name="bookings")
