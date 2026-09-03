"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-03 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # 2. User Sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('login_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_sessions_id', 'user_sessions', ['id'], unique=False)
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)

    # 3. Traffic Reports table
    op.create_table(
        'traffic_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('junction_id', sa.String(length=100), nullable=False),
        sa.Column('report_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('weather_condition', sa.String(length=50), nullable=True),
        sa.Column('congestion_level', sa.Float(), nullable=True),
        sa.Column('vehicle_count', sa.Integer(), nullable=True),
        sa.Column('pedestrian_count', sa.Integer(), nullable=True),
        sa.Column('railway_crossing_active', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_traffic_reports_junction_id', 'traffic_reports', ['junction_id'], unique=False)
    op.create_index('ix_traffic_reports_report_time', 'traffic_reports', ['report_time'], unique=False)
    op.create_index('ix_traffic_reports_user_id', 'traffic_reports', ['user_id'], unique=False)
    op.create_index('ix_traffic_reports_user_report_time', 'traffic_reports', ['user_id', 'report_time'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_traffic_reports_user_report_time', table_name='traffic_reports')
    op.drop_index('ix_traffic_reports_user_id', table_name='traffic_reports')
    op.drop_index('ix_traffic_reports_report_time', table_name='traffic_reports')
    op.drop_index('ix_traffic_reports_junction_id', table_name='traffic_reports')
    op.drop_table('traffic_reports')

    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_id', table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
