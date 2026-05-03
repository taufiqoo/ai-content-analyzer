"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'niche_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('keywords', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('hook_formulas', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('script_rules', sa.Text(), nullable=True),
        sa.Column('example_scripts', postgresql.JSON(), nullable=True),
        sa.Column('target_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'tweets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tweet_id', sa.String(50), nullable=False),
        sa.Column('author_username', sa.String(100), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('has_article_link', sa.Boolean(), nullable=True),
        sa.Column('article_url', sa.Text(), nullable=True),
        sa.Column('article_content', sa.Text(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('relevance_reason', sa.Text(), nullable=True),
        sa.Column('niche_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['niche_config_id'], ['niche_configs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tweet_id'),
    )

    op.create_table(
        'scripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tweet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('angle', sa.String(100), nullable=True),
        sa.Column('hook', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('cta', sa.Text(), nullable=False),
        sa.Column('full_script', sa.Text(), nullable=False),
        sa.Column('hook_formula_used', sa.String(200), nullable=True),
        sa.Column('duration_estimate', sa.Integer(), nullable=True),
        sa.Column('naturalness_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('claude_model', sa.String(50), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tweet_id'], ['tweets.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'script_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('script_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('watch_time_percent', sa.Float(), nullable=True),
        sa.Column('did_fyp', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'pipeline_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('celery_task_id', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('step', sa.String(100), nullable=True),
        sa.Column('tweets_fetched', sa.Integer(), nullable=True),
        sa.Column('tweets_relevant', sa.Integer(), nullable=True),
        sa.Column('scripts_generated', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('pipeline_jobs')
    op.drop_table('script_performance')
    op.drop_table('scripts')
    op.drop_table('tweets')
    op.drop_table('niche_configs')
