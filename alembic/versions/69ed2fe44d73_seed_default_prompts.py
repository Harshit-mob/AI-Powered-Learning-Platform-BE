"""seed_default_prompts

Revision ID: 69ed2fe44d73
Revises: 83ba33cebd44
Create Date: 2026-08-26 16:54:24.701053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69ed2fe44d73'
down_revision: Union[str, Sequence[str], None] = '83ba33cebd44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    import uuid
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent.parent
    prompts = {
        "question_generator": base_dir / "app" / "prompts" / "question_generator.md",
        "learning_unit_builder": base_dir / "app" / "prompts" / "learning_unit_builder.md"
    }
    
    connection = op.get_bind()
    
    for name, filepath in prompts.items():
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8").strip()
            connection.execute(
                sa.text(
                    "INSERT INTO system_prompts (id, name, content, created_at) "
                    "VALUES (:id, :name, :content, NOW()) "
                    "ON CONFLICT (name) DO NOTHING"
                ),
                {"id": str(uuid.uuid4()), "name": name, "content": content}
            )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM system_prompts WHERE name IN ('question_generator', 'learning_unit_builder')"
        )
    )
