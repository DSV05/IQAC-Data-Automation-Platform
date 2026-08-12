"""create excel_templates and excel_fill_logs tables

Revision ID: 007_excel_autofill
Revises: 006_reports
Create Date: 2024-01-07
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_excel_autofill"
down_revision: Union[str, None] = "006_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "excel_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("original_filename", sa.String(300), nullable=False),
        sa.Column("stored_filename", sa.String(300), nullable=False),
        sa.Column("sheet_count", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_excel_templates_uploaded_by", "excel_templates", ["uploaded_by"])

    op.create_table(
        "excel_fill_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("template_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("excel_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("tokens_filled", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_missing", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_excel_fill_logs_template_id", "excel_fill_logs", ["template_id"])
    op.create_index("ix_excel_fill_logs_user_id", "excel_fill_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("excel_fill_logs")
    op.drop_table("excel_templates")
