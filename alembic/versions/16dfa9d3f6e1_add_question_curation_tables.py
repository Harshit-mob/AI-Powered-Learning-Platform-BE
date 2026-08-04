"""add_question_curation_tables

Revision ID: 16dfa9d3f6e1
Revises: ea076b02af20
Create Date: 2026-08-04 18:25:13.539829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16dfa9d3f6e1'
down_revision: Union[str, Sequence[str], None] = 'ea076b02af20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create question_banks table
    op.create_table(
        'question_banks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('chapter_id', sa.UUID(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PROCESSING', nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create draft_questions table
    op.create_table(
        'draft_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('question_bank_id', sa.UUID(), nullable=False),
        sa.Column('learning_unit_id', sa.UUID(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('concept', sa.String(length=255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('mcq_options', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('correct_option', sa.String(length=255), nullable=True),
        sa.Column('answer_complexity', sa.String(length=50), server_default='WORD', nullable=True),
        sa.Column('evaluation_method', sa.String(length=50), server_default='WORD_MATCH', nullable=True),
        sa.Column('expected_answer', sa.Text(), nullable=True),
        sa.Column('acceptable_answers', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('difficulty', sa.Integer(), server_default='2', nullable=False),
        sa.Column('bloom_level', sa.String(length=50), nullable=True),
        sa.Column('cognitive_level', sa.String(length=50), nullable=True),
        sa.Column('hint_level_1', sa.Text(), nullable=True),
        sa.Column('hint_level_2', sa.Text(), nullable=True),
        sa.Column('full_explanation', sa.Text(), nullable=True),
        sa.Column('source_pages', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('keywords', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('question_purpose', sa.String(length=50), server_default='Practice', nullable=False),
        sa.Column('progression_level', sa.Integer(), server_default='3', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['learning_unit_id'], ['learning_units.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_bank_id'], ['question_banks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Alter questions table to add question_bank_id and is_active
    op.add_column('questions', sa.Column('question_bank_id', sa.UUID(), nullable=True))
    op.add_column('questions', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.create_foreign_key('fk_questions_question_bank', 'questions', 'question_banks', ['question_bank_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_questions_question_bank', 'questions', type_='foreignkey')
    op.drop_column('questions', 'is_active')
    op.drop_column('questions', 'question_bank_id')
    op.drop_table('draft_questions')
    op.drop_table('question_banks')
