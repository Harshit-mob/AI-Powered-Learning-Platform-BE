from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '168d1185ce16'
down_revision: Union[str, None] = 'a674345cd788'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.alter_column('questions', 'correct_option',
               existing_type=sa.VARCHAR(length=1),
               type_=sa.String(),
               existing_nullable=True)

def downgrade() -> None:
    op.alter_column('questions', 'correct_option',
               existing_type=sa.String(),
               type_=sa.VARCHAR(length=1),
               existing_nullable=True)
