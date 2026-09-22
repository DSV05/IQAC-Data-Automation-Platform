"""create custom_column_defs table

Revision ID: 011_custom_columns
Revises: 84aaf1c9e8d1
Create Date: 2026-09-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_custom_columns"
down_revision: Union[str, None] = "84aaf1c9e8d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_column_defs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("field_key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entity_type", "field_key", name="uq_custom_column_entity_key"),
    )
    op.create_index("ix_custom_column_defs_entity_type", "custom_column_defs", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_custom_column_defs_entity_type", table_name="custom_column_defs")
    op.drop_table("custom_column_defs")
