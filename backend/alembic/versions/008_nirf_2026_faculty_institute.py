"""add institute to faculty for official NIRF 2026 roster

Revision ID: 008_nirf_2026_faculty_institute
Revises: 007_excel_autofill
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_nirf_2026_faculty_institute"
down_revision: Union[str, None] = "007_excel_autofill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("faculty", sa.Column("institute", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("faculty", "institute")
