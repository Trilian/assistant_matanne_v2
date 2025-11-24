"""
Initial schema - All tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables"""

    # ===================================
    # USERS & PROFILES
    # ===================================

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('profile_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ===================================
    # CUISINE
    # ===================================

    op.create_table(
        'ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('prep_time', sa.Integer(), nullable=True),
        sa.Column('cook_time', sa.Integer(), nullable=True),
        sa.Column('servings', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('min_quantity', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('ai_alert_sent', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'shopping_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('needed_quantity', sa.Float(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('purchased', sa.Boolean(), nullable=True),
        sa.Column('ai_suggested', sa.Boolean(), nullable=True),
        sa.Column('store_section', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('purchased_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'batch_meals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('portions', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('ai_planned', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ===================================
    # FAMILLE
    # ===================================

    op.create_table(
        'child_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'wellbeing_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('mood', sa.String(length=50), nullable=False),
        sa.Column('sleep_hours', sa.Float(), nullable=True),
        sa.Column('activity', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('ai_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'routines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ai_suggested', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'routine_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('routine_id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(length=200), nullable=False),
        sa.Column('scheduled_time', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('ai_reminder_sent', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['routine_id'], ['routines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ===================================
    # MAISON
    # ===================================

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('ai_priority_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'project_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'garden_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('planting_date', sa.Date(), nullable=True),
        sa.Column('harvest_date', sa.Date(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('watering_frequency_days', sa.Integer(), nullable=True),
        sa.Column('last_watered', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ai_suggestions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'garden_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('weather_condition', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['garden_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ===================================
    # PLANNING & MÉTÉO
    # ===================================

    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('external_id', sa.String(length=500), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'weather_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('condition', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('humidity', sa.Integer(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('precipitation', sa.Float(), nullable=True),
        sa.Column('forecast_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_tasks_suggested', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )

    # ===================================
    # IA LOGS
    # ===================================

    op.create_table(
        'ai_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=200), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # ===================================
    # INDEXES
    # ===================================

    op.create_index('ix_recipes_category', 'recipes', ['category'])
    op.create_index('ix_recipes_ai_generated', 'recipes', ['ai_generated'])
    op.create_index('ix_inventory_items_quantity', 'inventory_items', ['quantity'])
    op.create_index('ix_batch_meals_scheduled_date', 'batch_meals', ['scheduled_date'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_calendar_events_start_date', 'calendar_events', ['start_date'])
    op.create_index('ix_ai_interactions_module', 'ai_interactions', ['module'])


def downgrade() -> None:
    """Drop all tables"""

    # Drop indexes
    op.drop_index('ix_ai_interactions_module')
    op.drop_index('ix_calendar_events_start_date')
    op.drop_index('ix_projects_status')
    op.drop_index('ix_batch_meals_scheduled_date')
    op.drop_index('ix_inventory_items_quantity')
    op.drop_index('ix_recipes_ai_generated')
    op.drop_index('ix_recipes_category')

    # Drop tables (in reverse order of dependencies)
    op.drop_table('ai_interactions')
    op.drop_table('weather_logs')
    op.drop_table('calendar_events')
    op.drop_table('garden_logs')
    op.drop_table('garden_items')
    op.drop_table('project_tasks')
    op.drop_table('projects')
    op.drop_table('routine_tasks')
    op.drop_table('routines')
    op.drop_table('wellbeing_entries')
    op.drop_table('child_profiles')
    op.drop_table('batch_meals')
    op.drop_table('shopping_lists')
    op.drop_table('inventory_items')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')
    op.drop_table('ingredients')
    op.drop_table('notifications')
    op.drop_table('user_profiles')
    op.drop_table('users')