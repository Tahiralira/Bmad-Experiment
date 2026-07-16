"""add_created_at_updated_at_to_user

Revision ID: 848b1a80cc28
Revises: 1a31ce608336
Create Date: 2026-01-06 12:37:51.295197

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "848b1a80cc28"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at column with timezone awareness and database-level default
    op.add_column(
        "user",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("UPDATE \"user\" SET created_at = NOW() WHERE created_at IS NULL")
    op.alter_column("user", "created_at", nullable=False)

    # Add updated_at column with timezone awareness and database-level default
    op.add_column(
        "user",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )
    op.execute("UPDATE \"user\" SET updated_at = NOW() WHERE updated_at IS NULL")
    op.alter_column("user", "updated_at", nullable=False)

    # Create trigger function for auto-updating updated_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Create trigger on user table
    op.execute(
        """
        CREATE TRIGGER update_user_updated_at
        BEFORE UPDATE ON "user"
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )


def downgrade():
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS update_user_updated_at ON "user"')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop columns
    op.drop_column("user", "updated_at")
    op.drop_column("user", "created_at")
