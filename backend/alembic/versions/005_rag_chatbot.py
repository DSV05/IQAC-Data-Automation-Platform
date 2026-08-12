"""create rag_documents and rag_chat_logs tables

Revision ID: 005_rag_chatbot
Revises: 004_ai_search
Create Date: 2024-01-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_rag_chatbot"
down_revision: Union[str, None] = "004_ai_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "naac_ssr", "annual_report", "nirf_report", "policy", "other",
        name="ragdocumenttype",
    ).create(bind)
    postgresql.ENUM(
        "processing", "ready", "failed",
        name="ragdocumentstatus",
    ).create(bind)
    postgresql.ENUM(
        "success", "error",
        name="ragchatstatus",
    ).create(bind)

    op.create_table(
        "rag_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("original_filename", sa.String(300), nullable=False),
        sa.Column("stored_filename", sa.String(300), nullable=False),
        sa.Column("doc_type",
                  postgresql.ENUM("naac_ssr", "annual_report", "nirf_report", "policy", "other",
                          name="ragdocumenttype", create_type=False),
                  nullable=False, server_default="other"),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("status",
                  postgresql.ENUM("processing", "ready", "failed",
                          name="ragdocumentstatus", create_type=False),
                  nullable=False, server_default="processing"),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("vector_ids", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rag_documents_uploaded_by", "rag_documents", ["uploaded_by"])

    op.create_table(
        "rag_chat_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("sources", postgresql.JSONB, nullable=True),
        sa.Column("status",
                  postgresql.ENUM("success", "error", name="ragchatstatus", create_type=False),
                  nullable=False, server_default="success"),
        sa.Column("execution_ms", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rag_chat_logs_user_id", "rag_chat_logs", ["user_id"])
    op.create_index("ix_rag_chat_logs_created_at", "rag_chat_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("rag_chat_logs")
    op.drop_table("rag_documents")
    op.execute("DROP TYPE IF EXISTS ragchatstatus")
    op.execute("DROP TYPE IF EXISTS ragdocumentstatus")
    op.execute("DROP TYPE IF EXISTS ragdocumenttype")
