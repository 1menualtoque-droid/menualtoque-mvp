"""reinitializgin - Create all tables with Integer SERIAL PKs

Revision ID: 3f9afde04c3c
Revises: 
Create Date: 2025-12-14 10:39:29.714112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3f9afde04c3c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with Integer SERIAL primary keys."""
    
    # Create ENUM types first using raw SQL (IF NOT EXISTS requires manual check)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE food_type_enum AS ENUM ('simple', 'composite', 'variant');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE meal_type_enum AS ENUM ('breakfast', 'lunch', 'dinner', 'snack', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qty_unit_enum AS ENUM ('g', 'ml', 'portion');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_status_enum AS ENUM ('queued', 'running', 'completed', 'failed', 'canceled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('picture_url', sa.Text(), nullable=True),
        sa.Column('google_sub', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_sub', 'users', ['google_sub'], unique=True)
    
    # Refresh tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('jti', sa.String(length=64), nullable=True),
        sa.Column('revoked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_tokens_jti', 'refresh_tokens', ['jti'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)
    
    # Email tokens table
    op.create_table('email_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(length=128), nullable=True),
        sa.Column('purpose', sa.String(length=32), nullable=True),
        sa.Column('used', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_email_tokens_token', 'email_tokens', ['token'], unique=True)
    op.create_index('ix_email_tokens_user_id', 'email_tokens', ['user_id'], unique=False)
    
    # External sources table
    op.create_table('external_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=True),
        sa.Column('kind', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Unit conversions table
    op.create_table('unit_conversions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_unit', sa.Text(), nullable=False),
        sa.Column('to_unit', sa.Text(), nullable=False),
        sa.Column('factor', sa.Numeric(precision=20, scale=10), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_unit_conversions_from_to_lower', 'unit_conversions', 
                    [sa.text('lower(from_unit)'), sa.text('lower(to_unit)')], unique=True)
    
    # Audit logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.Text(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('diff', sa.JSON(), nullable=True),
        sa.Column('ts', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id', 'ts'], unique=False)
    
    # Daily summaries table
    op.create_table('daily_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('local_date', sa.Date(), nullable=False),
        sa.Column('meals_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_kcal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_carbs_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_protein_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_fat_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_fiber_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_sodium_mg', sa.Numeric(precision=12, scale=0), nullable=False, server_default='0'),
        sa.Column('pct_kcal_carbs', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('pct_kcal_protein', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('pct_kcal_fat', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'local_date')
    )
    op.create_index('idx_ds_user_date', 'daily_summaries', ['user_id', 'local_date'], unique=False)
    
    # Foods table (without computed column - will add via raw SQL)
    op.create_table('foods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', postgresql.ENUM('simple', 'composite', 'variant', name='food_type_enum', create_type=False), nullable=False, server_default='simple'),
        sa.Column('parent_food_id', sa.Integer(), nullable=True),
        sa.Column('kcal_per_100g', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('carbs_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('protein_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fat_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fiber_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('sodium_mg_per_100g', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('kcal_per_100ml', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('carbs_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('protein_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fat_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fiber_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('sodium_mg_per_100ml', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('extra_nutrients', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_food_id'], ['foods.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add computed search_vector column via raw SQL
    op.execute("""
        ALTER TABLE foods ADD COLUMN search_vector tsvector 
        GENERATED ALWAYS AS (to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(description,''))) STORED
    """)
    
    op.create_index('idx_foods_name', 'foods', ['name'], unique=False)
    op.create_index('idx_foods_search_gin', 'foods', ['search_vector'], unique=False, postgresql_using='gin')
    
    # Import jobs table
    op.create_table('import_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=True),
        sa.Column('source_uri', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('queued', 'running', 'completed', 'failed', 'canceled', name='job_status_enum', create_type=False), nullable=False, server_default='queued'),
        sa.Column('imported_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['external_sources.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['started_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_jobs_source', 'import_jobs', ['source_id'], unique=False)
    
    # User consumptions table
    op.create_table('user_consumptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('local_date', sa.Date(), nullable=False),
        sa.Column('meal', postgresql.ENUM('breakfast', 'lunch', 'dinner', 'snack', 'other', name='meal_type_enum', create_type=False), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('total_kcal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_carbs_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_protein_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_fat_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_fiber_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('total_sodium_mg', sa.Numeric(precision=12, scale=0), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_uc_user_date', 'user_consumptions', ['user_id', 'local_date'], unique=False)
    op.create_index('idx_uc_user_time', 'user_consumptions', ['user_id', 'occurred_at'], unique=False)
    
    # User custom foods table
    op.create_table('user_custom_foods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('kcal_per_100g', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('carbs_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('protein_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fat_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fiber_g_per_100g', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('sodium_mg_per_100g', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('kcal_per_100ml', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('carbs_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('protein_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fat_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('fiber_g_per_100ml', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('sodium_mg_per_100ml', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('extra_nutrients', sa.JSON(), nullable=True),
        sa.Column('is_temporary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ucf_name', 'user_custom_foods', ['name'], unique=False)
    op.create_index('idx_ucf_user', 'user_custom_foods', ['user_id'], unique=False)
    
    # External food map table
    op.create_table('external_food_map',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.Text(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['external_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', 'external_id')
    )
    
    # Food aliases table
    op.create_table('food_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_food_alias', 'food_aliases', ['alias'], unique=False)
    
    # Food portions table
    op.create_table('food_portions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('grams_equivalent', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('ml_equivalent', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_food_portions_food', 'food_portions', ['food_id'], unique=False)
    
    # Food modifier groups table
    op.create_table('food_modifier_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_exclusive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('min_select', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_select', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Food versions table
    op.create_table('food_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('food_id', 'version')
    )
    
    # Import job items table
    op.create_table('import_job_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('line_no', sa.Integer(), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('queued', 'running', 'completed', 'failed', 'canceled', name='job_status_enum', create_type=False), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('food_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['import_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_items_job', 'import_job_items', ['job_id'], unique=False)
    
    # Consumption items table
    op.create_table('consumption_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consumption_id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=True),
        sa.Column('custom_food_id', sa.Integer(), nullable=True),
        sa.Column('original_name', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('unit', postgresql.ENUM('g', 'ml', 'portion', name='qty_unit_enum', create_type=False), nullable=True),
        sa.Column('portion_id', sa.Integer(), nullable=True),
        sa.Column('original_portion_label', sa.Text(), nullable=True),
        sa.Column('grams', sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column('ml', sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column('using_food_version', sa.Integer(), nullable=True),
        sa.Column('kcal', sa.Integer(), nullable=False),
        sa.Column('carbs_g', sa.Numeric(precision=10, scale=1), nullable=False),
        sa.Column('protein_g', sa.Numeric(precision=10, scale=1), nullable=False),
        sa.Column('fat_g', sa.Numeric(precision=10, scale=1), nullable=False),
        sa.Column('fiber_g', sa.Numeric(precision=10, scale=1), nullable=False, server_default='0'),
        sa.Column('sodium_mg', sa.Numeric(precision=12, scale=0), nullable=False, server_default='0'),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['consumption_id'], ['user_consumptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['custom_food_id'], ['user_custom_foods.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['portion_id'], ['food_portions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ci_consumption', 'consumption_items', ['consumption_id'], unique=False)
    op.create_index('idx_ci_custom', 'consumption_items', ['custom_food_id'], unique=False)
    op.create_index('idx_ci_food', 'consumption_items', ['food_id'], unique=False)
    
    # Food components table
    op.create_table('food_components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=5), nullable=False),
        sa.Column('unit', postgresql.ENUM('g', 'ml', 'portion', name='qty_unit_enum', create_type=False), nullable=False),
        sa.Column('portion_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['foods.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['portion_id'], ['food_portions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('food_id', 'component_id', 'portion_id', 'unit')
    )
    op.create_index('idx_components_child', 'food_components', ['component_id'], unique=False)
    op.create_index('idx_components_parent', 'food_components', ['food_id'], unique=False)
    
    # Food modifiers table
    op.create_table('food_modifiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('modifier_food_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['food_modifier_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modifier_food_id'], ['foods.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'modifier_food_id', name='uq_food_modifiers_group_modifier')
    )


def downgrade() -> None:
    """Drop all tables."""
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
    op.drop_table('email_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS food_type_enum')
    op.execute('DROP TYPE IF EXISTS meal_type_enum')
    op.execute('DROP TYPE IF EXISTS qty_unit_enum')
    op.execute('DROP TYPE IF EXISTS job_status_enum')
