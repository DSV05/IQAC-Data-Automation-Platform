"""add is_full_time + graduation_year to students

Needed for the NIRF "Ph.D. Students" and "Graduated Ph.D. Students" grids,
which split full-time vs part-time and break graduations down by year —
there was previously no field on Student to capture either.

Revision ID: 014_student_phd_fields
Revises: 013_custom_fields_column
Create Date: 2026-09-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_student_phd_fields"
down_revision: Union[str, None] = "013_custom_fields_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("students", sa.Column("is_full_time", sa.Boolean(), nullable=True))
    op.execute("UPDATE students SET is_full_time = true WHERE is_full_time IS NULL")
    op.alter_column("students", "is_full_time", nullable=False, server_default=sa.true())

    op.add_column("students", sa.Column("graduation_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("students", "graduation_year")
    op.drop_column("students", "is_full_time")
