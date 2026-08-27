"""add_source_type_to_topics

Revision ID: e329b8354b43
Revises: c223c096ef10
Create Date: 2026-08-27 12:41:15.213103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e329b8354b43'
down_revision: Union[str, Sequence[str], None] = 'c223c096ef10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'topics',
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='AI_GENERATED')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('topics', 'source_type')
