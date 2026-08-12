"""create auth tables

Revision ID: 001_auth
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_auth"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- departments -----------------------------------------------------------
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )

    # -- user_role enum --------------------------------------------------------
    user_role_enum = postgresql.ENUM(
        "super_admin", "iqac_admin", "department_coordinator",
        "data_entry_operator", "viewer",
        name="userrole",
    )
    user_role_enum.create(op.get_bind())

    # -- users -----------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("super_admin", "iqac_admin", "department_coordinator", "data_entry_operator", "viewer", name="userrole", create_type=False), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reset_token", sa.String(255), nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_department_id", "users", ["department_id"])

    # -- refresh_tokens --------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    # -- Seed initial departments for Ganpat University ------------------------
    op.execute("""
        INSERT INTO departments (id, name, code, description) VALUES
        (uuid_generate_v4(), 'Computer Engineering', 'CE', 'Department of Computer Engineering'),
        (uuid_generate_v4(), 'Mechanical Engineering', 'ME', 'Department of Mechanical Engineering'),
        (uuid_generate_v4(), 'Civil Engineering', 'CIV', 'Department of Civil Engineering'),
        (uuid_generate_v4(), 'Electrical Engineering', 'EE', 'Department of Electrical Engineering'),
        (uuid_generate_v4(), 'Electronics & Communication', 'EC', 'Department of Electronics & Communication'),
        (uuid_generate_v4(), 'Information Technology', 'IT', 'Department of Information Technology'),
        (uuid_generate_v4(), 'MBA', 'MBA', 'Master of Business Administration'),
        (uuid_generate_v4(), 'Pharmacy', 'PHARM', 'Department of Pharmacy'),
        (uuid_generate_v4(), 'IQAC', 'IQAC', 'Internal Quality Assurance Cell')
    """)


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("departments")
    op.execute("DROP TYPE IF EXISTS userrole")
