"""Add StudentDailyLearning

Revision ID: 591e8de84c24
Revises: b75e95c29369
Create Date: 2026-07-15 10:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '591e8de84c24'
down_revision: Union[str, None] = 'b75e95c29369'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('student_daily_learning',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('student_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('topic_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('learning_date', sa.Date(), autoincrement=False, nullable=False),
    sa.Column('source', sa.String(), autoincrement=False, nullable=False, server_default='SCHOOL'),
    sa.Column('status', sa.String(), autoincrement=False, nullable=False, server_default='PENDING'),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('student_daily_learning')
