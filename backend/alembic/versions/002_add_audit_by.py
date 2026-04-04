"""Add created_by / updated_by audit columns (already applied to DB).

Revision ID: 002_add_audit_by
Revises: 001_baseline
Create Date: applied manually
"""

from typing import Sequence, Union

# revision identifiers
revision: str = "002_add_audit_by"
down_revision: Union[str, Sequence[str], None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass  # already applied directly to DB


def downgrade() -> None:
    pass
