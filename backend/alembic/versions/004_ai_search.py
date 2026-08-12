"""create ai_query_logs table

Revision ID: 004_ai_search
Revises: 003_uploads
Create Date: 2024-01-04
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_ai_search"
down_revision: Union[str, None] = "003_uploads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "success", "blocked", "error",
        name="aiquerystatus",
    ).create(bind)

    op.create_table(
        "ai_query_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("generated_sql", sa.Text, nullable=True),
        sa.Column("status",
                  postgresql.ENUM("success", "blocked", "error",
                          name="aiquerystatus", create_type=False),
                  nullable=False, server_default="success"),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("execution_ms", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_query_logs_user_id", "ai_query_logs", ["user_id"])
    op.create_index("ix_ai_query_logs_created_at", "ai_query_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("ai_query_logs")
    op.execute("DROP TYPE IF EXISTS aiquerystatus")
