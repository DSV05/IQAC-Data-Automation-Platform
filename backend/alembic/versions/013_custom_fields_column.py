"""add custom_fields JSONB to every table (BaseModel now declares it)

Every model extends BaseModel, which now carries a nullable `custom_fields`
JSONB column so admin-added "+ Add Column" values (see custom_column.py)
have somewhere to live on the actual record, not just as a blank header in
the downloaded template. Added everywhere rather than only on the 14
upload-eligible entities, since the SQLAlchemy model declares it
universally and every mapped table must match.

Revision ID: 013_custom_fields_column
Revises: 012_student_level
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013_custom_fields_column"
down_revision: Union[str, None] = "012_student_level"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "ai_query_logs", "audit_logs", "awards", "accreditations", "consultancies",
    "sdg_activities", "custom_column_defs", "excel_templates", "excel_fill_logs",
    "faculty", "energy_consumption", "water_consumption", "waste_management",
    "green_initiatives", "infrastructure", "budgets", "mous", "events",
    "notifications", "deadlines", "placements", "higher_studies",
    "rag_documents", "rag_chat_logs", "report_generation_logs",
    "research_publications", "patents", "funded_projects", "programs",
    "students", "upload_jobs", "departments", "users", "refresh_tokens",
    "workflow_submissions", "workflow_history",
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS custom_fields JSONB')


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS custom_fields')
