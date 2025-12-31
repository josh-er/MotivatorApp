"""make users.time nullable

Revision ID: make_users_time_nullable
Revises: add_timezone_fields
Create Date: 2025-12-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "make_users_time_nullable"
down_revision = "add_timezone_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "users",
        "time",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "users",
        "time",
        existing_type=sa.String(),
        nullable=False,
    )
