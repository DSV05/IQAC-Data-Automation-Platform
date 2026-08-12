"""create workflow_submissions and workflow_history tables

Revision ID: 008_workflow
Revises: 007_excel_autofill
Create Date: 2024-01-08
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_workflow"
down_revision: Union[str, None] = "007_excel_autofill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "draft", "submitted", "approved", "rejected", "locked",
        name="workflowstatus",
    ).create(bind)

    op.create_table(
        "workflow_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("department_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("status",
                  postgresql.ENUM("draft", "submitted", "approved", "rejected", "locked",
                          name="workflowstatus", create_type=False),
                  nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comments", sa.Text, nullable=True),
        sa.Column("locked_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("department_id", "academic_year", name="uq_workflow_dept_year"),
    )
    op.create_index("ix_workflow_submissions_department_id", "workflow_submissions", ["department_id"])
    op.create_index("ix_workflow_submissions_academic_year", "workflow_submissions", ["academic_year"])

    op.create_table(
        "workflow_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("workflow_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status",
                  postgresql.ENUM("draft", "submitted", "approved", "rejected", "locked",
                          name="workflowstatus", create_type=False),
                  nullable=True),
        sa.Column("to_status",
                  postgresql.ENUM("draft", "submitted", "approved", "rejected", "locked",
                          name="workflowstatus", create_type=False),
                  nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_history_submission_id", "workflow_history", ["submission_id"])


def downgrade() -> None:
    op.drop_table("workflow_history")
    op.drop_table("workflow_submissions")
    op.execute("DROP TYPE IF EXISTS workflowstatus")
