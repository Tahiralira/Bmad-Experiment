"""add_auth_method_to_user

Revision ID: a3c7d2e1f4b5
Revises: 52b6a1b5166e
Create Date: 2026-01-07 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3c7d2e1f4b5'
down_revision = '52b6a1b5166e'
branch_labels = None
depends_on = None


def upgrade():
    # Add auth_method column to user table
    # Default is 'password' for existing users
    op.add_column(
        'user',
        sa.Column('auth_method', sa.String(length=20), nullable=True)
    )
    # Set default for existing users
    op.execute("UPDATE \"user\" SET auth_method = 'password' WHERE auth_method IS NULL")
    # Make column non-nullable
    op.alter_column('user', 'auth_method', nullable=False, server_default='password')


def downgrade():
    op.drop_column('user', 'auth_method')
