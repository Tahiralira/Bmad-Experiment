"""add_oauth_fields_to_user

Revision ID: b4d8e2f5a6c9
Revises: a3c7d2e1f4b5
Create Date: 2026-01-07 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d8e2f5a6c9'
down_revision = 'a3c7d2e1f4b5'
branch_labels = None
depends_on = None


def upgrade():
    # Add oauth_provider column to user table
    op.add_column(
        'user',
        sa.Column('oauth_provider', sa.String(length=50), nullable=True)
    )
    # Add oauth_provider_id column to user table
    op.add_column(
        'user',
        sa.Column('oauth_provider_id', sa.String(length=255), nullable=True)
    )
    # Create unique index for OAuth lookups (provider + provider_id combination)
    op.create_index(
        'ix_user_oauth_provider_id',
        'user',
        ['oauth_provider', 'oauth_provider_id'],
        unique=True,
        postgresql_where=sa.text('oauth_provider IS NOT NULL')
    )


def downgrade():
    op.drop_index('ix_user_oauth_provider_id', 'user')
    op.drop_column('user', 'oauth_provider_id')
    op.drop_column('user', 'oauth_provider')
