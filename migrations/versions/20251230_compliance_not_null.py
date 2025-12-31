from alembic import op
import sqlalchemy as sa

revision = "20251230_compliance_not_null"
down_revision = "make_users_time_nullable"
branch_labels = None
depends_on = None


def upgrade():
    # Backfill existing NULLs
    op.execute(
        "UPDATE users SET opted_in = TRUE WHERE opted_in IS NULL"
    )
    op.execute(
        "UPDATE users SET received_compliance = FALSE WHERE received_compliance IS NULL"
    )

    # Set server defaults
    op.alter_column(
        "users",
        "opted_in",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )

    op.alter_column(
        "users",
        "received_compliance",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )


def downgrade():
    # Allow NULLs again
    op.alter_column(
        "users",
        "opted_in",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )

    op.alter_column(
        "users",
        "received_compliance",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
