"""remove utc_time from users

Revision ID: 4f24a0dddd89
Revises: 4cf91fb152a0
Create Date: 2026-01-24 22:15:25.950119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f24a0dddd89'
down_revision: Union[str, Sequence[str], None] = '4cf91fb152a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "utc_time")


def downgrade() -> None:
    op.add_column(
    "users",
    sa.Column("utc_time", sa.String(), nullable=True)
)
