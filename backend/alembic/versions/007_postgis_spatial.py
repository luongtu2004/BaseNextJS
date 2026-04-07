"""Add PostGIS GEOGRAPHY(POINT) columns for spatial queries.

Revision ID: 007_postgis_spatial
Revises: 006_perf_indexes
Create Date: 2026-04-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision: str = "007_postgis_spatial"
down_revision: Union[str, Sequence[str], None] = "006_perf_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # Check if 'location' column already exists on driver_locations
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name='driver_locations' AND column_name='location'"
    ))
    has_location = result.fetchone() is not None

    if not has_location:
        # 2. Add geography column to driver_locations
        op.add_column("driver_locations", sa.Column(
            "location", Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ))
        
        # 3. Add geography column to bookings (pickup + dropoff)
        op.add_column("bookings", sa.Column(
            "pickup_point", Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ))
        op.add_column("bookings", sa.Column(
            "dropoff_point", Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ))

        # 4. Backfill from existing Numeric columns
        op.execute("""
            UPDATE driver_locations
            SET location = ST_SetSRID(ST_MakePoint(longitude::float, latitude::float), 4326)::geography
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        op.execute("""
            UPDATE bookings
            SET pickup_point = ST_SetSRID(ST_MakePoint(pickup_lng::float, pickup_lat::float), 4326)::geography
            WHERE pickup_lat IS NOT NULL AND pickup_lng IS NOT NULL
        """)
        op.execute("""
            UPDATE bookings
            SET dropoff_point = ST_SetSRID(ST_MakePoint(dropoff_lng::float, dropoff_lat::float), 4326)::geography
            WHERE dropoff_lat IS NOT NULL AND dropoff_lng IS NOT NULL
        """)

        # 5. Create GIST spatial indexes manually to ensure IF NOT EXISTS semantics
        op.execute("CREATE INDEX IF NOT EXISTS gix_driver_locations_loc ON driver_locations USING gist (location);")
        op.execute("CREATE INDEX IF NOT EXISTS gix_bookings_pickup ON bookings USING gist (pickup_point);")
        op.execute("CREATE INDEX IF NOT EXISTS gix_bookings_dropoff ON bookings USING gist (dropoff_point);")

        # 6. Compound GIST index for hot query: pending bookings near driver
        op.execute("""
            CREATE INDEX IF NOT EXISTS gix_bookings_pending_pickup
            ON bookings USING gist (pickup_point)
            WHERE status = 'pending' AND pickup_point IS NOT NULL;
        """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gix_bookings_pending_pickup;")
    op.execute("DROP INDEX IF EXISTS gix_bookings_dropoff;")
    op.execute("DROP INDEX IF EXISTS gix_bookings_pickup;")
    op.execute("DROP INDEX IF EXISTS gix_driver_locations_loc;")
    
    op.drop_column("bookings", "dropoff_point")
    op.drop_column("bookings", "pickup_point")
    op.drop_column("driver_locations", "location")
