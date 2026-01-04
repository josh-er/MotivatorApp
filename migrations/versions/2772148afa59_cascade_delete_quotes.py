"""cascade delete quotes

Revision ID: 2772148afa59
Revises: 98555a134813
Create Date: 2026-01-04 13:24:23.892440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# cascade delete sent_quotes when quote deleted

# revision identifiers, used by Alembic.
revision: str = '2772148afa59'
down_revision: Union[str, Sequence[str], None] = '98555a134813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint("sent_quotes_quote_id_fkey", "sent_quotes", type_="foreignkey")
    op.create_foreign_key(
        None,
        "sent_quotes",
        "quotes",
        ["quote_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        None,  # Alembic generated FK name
        "sent_quotes",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "sent_quotes_quote_id_fkey",
        "sent_quotes",
        "quotes",
        ["quote_id"],
        ["id"],
    )
