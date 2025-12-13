"""add timezone/local_time/utc_time to users

Revision ID: add_timezone_fields
Revises: 6d24f58aa477
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_timezone_fields'
down_revision = '6d24f58aa477'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('local_time', sa.String(), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('utc_time', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'utc_time')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'local_time')
