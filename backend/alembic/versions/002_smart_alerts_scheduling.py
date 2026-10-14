"""Smart Login Alerts, Daily Scheduling, and Email Delivery Logs

Revision ID: 002_smart_alerts
Revises: 001_initial
Create Date: 2026-10-14 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_smart_alerts'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend alerts table with deduplication and tracking columns
    op.add_column('alerts', sa.Column('relevant_stock_quantity', sa.Float(), nullable=True))
    op.add_column('alerts', sa.Column('relevant_expiry_date', sa.Date(), nullable=True))
    op.add_column('alerts', sa.Column('status', sa.String(length=50), server_default='active', nullable=False))
    op.add_column('alerts', sa.Column('first_detected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('alerts', sa.Column('last_checked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('alerts', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('alerts', sa.Column('deduplication_key', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)
    op.create_index(op.f('ix_alerts_deduplication_key'), 'alerts', ['deduplication_key'], unique=True)

    # 2. Notification Settings table
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('shop_id', sa.String(length=100), server_default='default_shop', nullable=False),
        sa.Column('recipient_emails', sa.Text(), server_default='', nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('report_frequency', sa.String(length=50), server_default='daily', nullable=False),
        sa.Column('scheduled_time', sa.String(length=20), server_default='08:00', nullable=False),
        sa.Column('timezone', sa.String(length=100), server_default='Asia/Kolkata', nullable=False),
        sa.Column('categories', sa.String(length=255), server_default='near_expiry,low_stock,out_of_stock,sales_summary', nullable=False),
        sa.Column('include_empty_reports', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_settings_id'), 'notification_settings', ['id'], unique=False)
    op.create_index(op.f('ix_notification_settings_shop_id'), 'notification_settings', ['shop_id'], unique=False)

    # 3. Scheduled Job Runs table
    op.create_table(
        'scheduled_job_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(length=100), server_default='daily_inventory_check', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='running', nullable=False),
        sa.Column('summary_counts', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_job_runs_id'), 'scheduled_job_runs', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_job_runs_job_name'), 'scheduled_job_runs', ['job_name'], unique=False)
    op.create_index(op.f('ix_scheduled_job_runs_status'), 'scheduled_job_runs', ['status'], unique=False)

    # 4. Email Delivery Logs table
    op.create_table(
        'email_delivery_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('scheduled_run_id', sa.Integer(), sa.ForeignKey('scheduled_job_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('attempt_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='queued', nullable=False),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_delivery_logs_id'), 'email_delivery_logs', ['id'], unique=False)
    op.create_index(op.f('ix_email_delivery_logs_report_type'), 'email_delivery_logs', ['report_type'], unique=False)
    op.create_index(op.f('ix_email_delivery_logs_recipient'), 'email_delivery_logs', ['recipient'], unique=False)
    op.create_index(op.f('ix_email_delivery_logs_idempotency_key'), 'email_delivery_logs', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_email_delivery_logs_status'), 'email_delivery_logs', ['status'], unique=False)

    # 5. Daily Inventory Snapshots table
    op.create_table(
        'daily_inventory_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reporting_date', sa.Date(), nullable=False),
        sa.Column('near_expiry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('low_stock_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('out_of_stock_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_stock_value', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('sales_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('revenue', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('gross_profit', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('generation_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_inventory_snapshots_id'), 'daily_inventory_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_daily_inventory_snapshots_reporting_date'), 'daily_inventory_snapshots', ['reporting_date'], unique=True)


def downgrade() -> None:
    op.drop_table('daily_inventory_snapshots')
    op.drop_table('email_delivery_logs')
    op.drop_table('scheduled_job_runs')
    op.drop_table('notification_settings')
    op.drop_index(op.f('ix_alerts_deduplication_key'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_status'), table_name='alerts')
    op.drop_column('alerts', 'deduplication_key')
    op.drop_column('alerts', 'read_at')
    op.drop_column('alerts', 'last_checked_at')
    op.drop_column('alerts', 'first_detected_at')
    op.drop_column('alerts', 'status')
    op.drop_column('alerts', 'relevant_expiry_date')
    op.drop_column('alerts', 'relevant_stock_quantity')
