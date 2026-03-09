"""remove_food_consumption_nutrition_tables

Revision ID: b319f9eab37e
Revises: 5fe9a3ef9c78
Create Date: 2026-03-08 21:40:10.538710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b319f9eab37e'
down_revision: Union[str, Sequence[str], None] = '5fe9a3ef9c78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove all food, consumption, and nutrition related tables."""
    
    # Drop tables with foreign key dependencies first (children before parents)
    op.drop_table('food_modifiers')
    op.drop_table('food_components')
    op.drop_table('consumption_items')
    op.drop_table('import_job_items')
    op.drop_table('food_versions')
    op.drop_table('food_modifier_groups')
    op.drop_table('food_portions')
    op.drop_table('food_aliases')
    op.drop_table('external_food_map')
    op.drop_table('user_custom_foods')
    op.drop_table('user_consumptions')
    op.drop_table('import_jobs')
    op.drop_table('foods')
    op.drop_table('daily_summaries')
    op.drop_table('audit_logs')
    op.drop_table('unit_conversions')
    op.drop_table('external_sources')
    
    # Drop ENUM types that are no longer needed
    op.execute('DROP TYPE IF EXISTS food_type_enum')
    op.execute('DROP TYPE IF EXISTS meal_type_enum')
    op.execute('DROP TYPE IF EXISTS qty_unit_enum')
    op.execute('DROP TYPE IF EXISTS job_status_enum')


def downgrade() -> None:
    """Downgrade schema."""
    pass
