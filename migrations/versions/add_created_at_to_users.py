"""add created_at to users

Revision ID: add_created_at_to_users
Revises: add_event_logs
Branch Labels: None
Depends On: None

"""
from alembic import op
import sqlalchemy as sa


revision = "add_created_at_to_users"
down_revision = "add_event_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_column("users", "created_at")
