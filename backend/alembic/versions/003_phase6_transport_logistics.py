"""Phase 6: Transport & Logistics — Create provider_vehicles, provider_vehicle_documents,
service_routes, service_route_schedules, provider_vehicle_availabilities.

Revision ID: 002_phase6_transport
Revises: 001_baseline
Create Date: 2026-04-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "003_phase6_transport"
down_revision: Union[str, Sequence[str], None] = "002_add_audit_by"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── provider_vehicles ─────────────────────────────────────────────
    op.create_table(
        "provider_vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("provider_services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vehicle_type", sa.String(50), nullable=False),
        sa.Column("vehicle_brand", sa.String(100), nullable=True),
        sa.Column("vehicle_model", sa.String(100), nullable=True),
        sa.Column("year_of_manufacture", sa.Integer(), nullable=True),
        sa.Column("license_plate", sa.String(20), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=True),
        sa.Column("fuel_type", sa.String(20), nullable=True),
        sa.Column("transmission", sa.String(20), nullable=True),
        sa.Column("has_ac", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_wifi", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("color", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_provider_vehicles_provider_id", "provider_vehicles", ["provider_id"])

    # ── provider_vehicle_documents ────────────────────────────────────
    op.create_table(
        "provider_vehicle_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("provider_vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(20), nullable=False,
                  server_default=sa.text("'pending'")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_pvd_vehicle_id", "provider_vehicle_documents", ["vehicle_id"])
    op.create_index("ix_pvd_review_status", "provider_vehicle_documents", ["review_status"])

    # ── service_routes ────────────────────────────────────────────────
    op.create_table(
        "service_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider_service_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("provider_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_province", sa.String(100), nullable=False),
        sa.Column("to_province", sa.String(100), nullable=False),
        sa.Column("distance_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(18, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_service_routes_svc_id", "service_routes", ["provider_service_id"])
    op.create_index("ix_service_routes_from_to",
                    "service_routes", ["from_province", "to_province"])

    # ── service_route_schedules ───────────────────────────────────────
    op.create_table(
        "service_route_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("route_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("service_routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("departure_time", sa.Time(), nullable=False),
        sa.Column("seat_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_srs_route_id", "service_route_schedules", ["route_id"])
    # Prevent duplicate departure times on the same route
    op.create_unique_constraint(
        "uq_schedule_route_time", "service_route_schedules", ["route_id", "departure_time"]
    )

    # ── provider_vehicle_availabilities ──────────────────────────────
    op.create_table(
        "provider_vehicle_availabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("provider_vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("vehicle_id", "date", name="uq_vehicle_availability_date"),
    )
    op.create_index("ix_pva_vehicle_id", "provider_vehicle_availabilities", ["vehicle_id"])
    op.create_index("ix_pva_date", "provider_vehicle_availabilities", ["date"])


def downgrade() -> None:
    op.drop_table("provider_vehicle_availabilities")
    op.drop_table("service_route_schedules")
    op.drop_table("service_routes")
    op.drop_table("provider_vehicle_documents")
    op.drop_table("provider_vehicles")
