"""add_user_onboarding_fields

Revision ID: 5fe9a3ef9c78
Revises: 3f9afde04c3c
Create Date: 2026-03-07 01:10:59.501634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fe9a3ef9c78'
down_revision: Union[str, Sequence[str], None] = '3f9afde04c3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('needs_nutritional_plan', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('sex', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('height_cm', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('weight_kg', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('activity_level', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('sport', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('goals', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('available_foods', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('target_calories', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'target_calories')
    op.drop_column('users', 'available_foods')
    op.drop_column('users', 'goals')
    op.drop_column('users', 'sport')
    op.drop_column('users', 'activity_level')
    op.drop_column('users', 'weight_kg')
    op.drop_column('users', 'height_cm')
    op.drop_column('users', 'sex')
    op.drop_column('users', 'needs_nutritional_plan')
    op.drop_column('users', 'onboarding_completed_at')
    op.drop_column('users', 'onboarding_completed')
