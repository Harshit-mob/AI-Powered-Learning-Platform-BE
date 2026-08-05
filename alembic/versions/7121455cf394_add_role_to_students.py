"""add_role_to_students

Revision ID: 7121455cf394
Revises: 16dfa9d3f6e1
Create Date: 2026-08-05 11:12:04.597802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7121455cf394'
down_revision: Union[str, Sequence[str], None] = '16dfa9d3f6e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('role', sa.String(length=50), server_default='STUDENT', nullable=False))


def downgrade() -> None:
    op.drop_column('students', 'role')
