"""create initial tables

Revision ID: 17e89bfd1c7f
Revises: 
Create Date: 2025-09-14 19:26:35.014288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "17e89bfd1c7f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("phone", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("time", sa.String(), nullable=False),  # format "HH:MM"
        sa.Column("last_sent", sa.Date(), nullable=True),
        sa.Column("cycle", sa.Integer(), nullable=False, server_default="1"),
    )

    # quotes table
    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("text", sa.String(), nullable=False),
    )

    # message_logs table
    op.create_table(
        "message_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("quote", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # sent_quotes table
    op.create_table(
        "sent_quotes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id"), nullable=False),
        sa.Column("sent_date", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "quote_id", name="_user_quote_uc"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("sent_quotes")
    op.drop_table("message_logs")
    op.drop_table("quotes")
    op.drop_table("users")
