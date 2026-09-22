"""remove program_id from students, add level + duration_years

Program is no longer linked to individual students — a student now just
carries its own Level (UG/PG/Diploma/...) and Duration directly, so
uploads don't need an exact Program code to already exist for the
department/year. The Programs table itself is untouched: it still holds
sanctioned/actual intake numbers (grouped by level + duration) that feed
the NIRF template's intake grid.

Revision ID: 012_student_level
Revises: 011_custom_columns
Create Date: 2026-09-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_student_level"
down_revision: Union[str, None] = "011_custom_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROGRAM_LEVEL = postgresql.ENUM(
    "diploma", "ug", "pg", "phd", "certificate",
    name="programlevel", create_type=False,
)


def upgrade() -> None:
    op.add_column("students", sa.Column("level", PROGRAM_LEVEL, nullable=True))
    op.add_column("students", sa.Column("duration_years", sa.Integer(), nullable=True))

    # Best-effort backfill from the old program_id link before dropping it,
    # so existing rows don't lose their level/duration outright.
    op.execute(
        """
        UPDATE students
        SET level = programs.level, duration_years = programs.duration_years
        FROM programs
        WHERE students.program_id = programs.id
        """
    )
    # Anything left unmatched (orphaned program_id, or none at all) defaults
    # to UG / 4 years so the column can be made NOT NULL.
    op.execute("UPDATE students SET level = 'ug' WHERE level IS NULL")
    op.execute("UPDATE students SET duration_years = 4 WHERE duration_years IS NULL")

    op.alter_column("students", "level", nullable=False)
    op.alter_column("students", "duration_years", nullable=False)

    op.drop_constraint("students_program_id_fkey", "students", type_="foreignkey")
    op.drop_column("students", "program_id")


def downgrade() -> None:
    op.add_column("students", sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("students_program_id_fkey", "students", "programs", ["program_id"], ["id"])
    op.drop_column("students", "duration_years")
    op.drop_column("students", "level")
