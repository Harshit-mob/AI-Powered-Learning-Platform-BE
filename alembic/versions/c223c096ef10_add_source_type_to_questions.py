"""add_source_type_to_questions

Revision ID: c223c096ef10
Revises: 69ed2fe44d73
Create Date: 2026-08-27 11:35:14.376864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c223c096ef10'
down_revision: Union[str, Sequence[str], None] = '69ed2fe44d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'questions',
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='AI_GENERATED')
    )
    op.add_column(
        'draft_questions',
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='AI_GENERATED')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('draft_questions', 'source_type')
    op.drop_column('questions', 'source_type')
