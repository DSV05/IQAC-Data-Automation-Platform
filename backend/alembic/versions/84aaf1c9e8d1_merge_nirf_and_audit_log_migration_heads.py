"""merge NIRF and audit log migration heads

Revision ID: 84aaf1c9e8d1
Revises: 008_nirf_2026_faculty_institute, 010_audit_logs
Create Date: 2026-09-09 05:25:57.718347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84aaf1c9e8d1'
down_revision: Union[str, None] = ('008_nirf_2026_faculty_institute', '010_audit_logs')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass