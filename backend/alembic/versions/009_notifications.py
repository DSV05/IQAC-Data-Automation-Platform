"""create notifications and deadlines tables

Revision ID: 009_notifications
Revises: 008_workflow
Create Date: 2024-01-09
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_notifications"
down_revision: Union[str, None] = "008_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "missing_data", "deadline_reminder", "workflow_submitted",
        "workflow_approved", "workflow_rejected", "workflow_locked", "general",
        name="notificationtype",
    ).create(bind)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type",
                  postgresql.ENUM("missing_data", "deadline_reminder", "workflow_submitted",
                          "workflow_approved", "workflow_rejected", "workflow_locked", "general",
                          name="notificationtype", create_type=False),
                  nullable=False, server_default="general"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("link", sa.String(300), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "deadlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("reminder_days_before", sa.Integer, nullable=False, server_default="3"),
        sa.Column("last_reminded_on", sa.Date, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deadlines_department_id", "deadlines", ["department_id"])


def downgrade() -> None:
    op.drop_table("deadlines")
    op.drop_table("notifications")
    op.execute("DROP TYPE IF EXISTS notificationtype")
