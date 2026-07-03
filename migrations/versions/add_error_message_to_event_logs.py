"""add error_message to event_logs

Revision ID: add_error_message_to_event_logs
Revises: add_created_at_to_users
Branch Labels: None
Depends On: None

"""
from alembic import op
import sqlalchemy as sa


revision = "add_error_message_to_event_logs"
down_revision = "add_created_at_to_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_logs",
        sa.Column(
            "error_message",
            sa.String(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("event_logs", "error_message")
