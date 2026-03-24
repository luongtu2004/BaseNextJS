"""Baseline: schema already applied via database.sql (empty upgrade).

If DB matches database.sql: run `alembic stamp head` once.
Future revisions add otp_sessions, refresh_tokens, etc.

Revision ID: 001_baseline
Revises:
Create Date: 2026-03-23

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
