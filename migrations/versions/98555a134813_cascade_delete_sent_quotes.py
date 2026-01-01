"""cascade delete sent_quotes

Revision ID: 98555a134813
Revises: 20251230_compliance_not_null
Create Date: 2026-01-01 13:56:11.784313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98555a134813'
down_revision: Union[str, Sequence[str], None] = '20251230_compliance_not_null'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# cascade delete sent_quotes on user delete"
def upgrade():
    op.drop_constraint(
        "sent_quotes_user_id_fkey",
        "sent_quotes",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "sent_quotes_user_id_fkey",
        "sent_quotes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "sent_quotes_user_id_fkey",
        "sent_quotes",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "sent_quotes_user_id_fkey",
        "sent_quotes",
        "users",
        ["user_id"],
        ["id"],
    )
