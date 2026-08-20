"""create audit_logs table

Revision ID: 010_audit_logs
Revises: 009_notifications
Create Date: 2024-01-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_audit_logs"
down_revision: Union[str, None] = "009_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("changed_by_name", sa.String(255), nullable=True),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual_edit"),
        sa.Column("changes", sa.JSON, nullable=False),
        sa.Column("entity_label", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_changed_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_academic_year", "audit_logs", ["academic_year"])


def downgrade() -> None:
    op.drop_table("audit_logs")
