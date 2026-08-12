"""create report_generation_logs table

Revision ID: 006_reports
Revises: 005_rag_chatbot
Create Date: 2024-01-06
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_reports"
down_revision: Union[str, None] = "005_rag_chatbot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM("nirf", "naac_ssr", "aishe", name="reporttype").create(bind)
    postgresql.ENUM("xlsx", "pdf", name="reportformat").create(bind)

    op.create_table(
        "report_generation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type",
                  postgresql.ENUM("nirf", "naac_ssr", "aishe", name="reporttype", create_type=False),
                  nullable=False),
        sa.Column("report_format",
                  postgresql.ENUM("xlsx", "pdf", name="reportformat", create_type=False),
                  nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_report_generation_logs_user_id", "report_generation_logs", ["user_id"])
    op.create_index("ix_report_generation_logs_created_at", "report_generation_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("report_generation_logs")
    op.execute("DROP TYPE IF EXISTS reportformat")
    op.execute("DROP TYPE IF EXISTS reporttype")
