"""create upload_jobs table

Revision ID: 003_uploads
Revises: 002_master_data
Create Date: 2024-01-03
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_uploads"
down_revision: Union[str, None] = "002_master_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "pending", "processing", "completed", "failed", "partial",
        name="uploadstatus",
    ).create(bind)

    postgresql.ENUM(
        "faculty", "students", "research", "patents", "placements",
        "higher_studies", "funded_projects", "mous", "events",
        "energy", "water", "waste", "awards", "consultancy", "sdg_activities",
        name="uploadentitytype",
    ).create(bind)

    op.create_table(
        "upload_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entity_type",
                  postgresql.ENUM("faculty","students","research","patents","placements",
                          "higher_studies","funded_projects","mous","events",
                          "energy","water","waste","awards","consultancy","sdg_activities",
                          name="uploadentitytype", create_type=False),
                  nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("status",
                  postgresql.ENUM("pending","processing","completed","failed","partial",
                          name="uploadstatus", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("inserted_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("validation_errors", postgresql.JSON, nullable=True),
        sa.Column("column_mapping", postgresql.JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_upload_jobs_uploaded_by", "upload_jobs", ["uploaded_by"])
    op.create_index("ix_upload_jobs_entity_type", "upload_jobs", ["entity_type"])
    op.create_index("ix_upload_jobs_status", "upload_jobs", ["status"])
    op.create_index("ix_upload_jobs_academic_year", "upload_jobs", ["academic_year"])


def downgrade() -> None:
    op.drop_table("upload_jobs")
    op.execute("DROP TYPE IF EXISTS uploadentitytype")
    op.execute("DROP TYPE IF EXISTS uploadstatus")
