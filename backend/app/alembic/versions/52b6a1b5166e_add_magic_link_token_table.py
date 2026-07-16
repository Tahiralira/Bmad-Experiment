"""add_magic_link_token_table

Revision ID: 52b6a1b5166e
Revises: 848b1a80cc28
Create Date: 2026-01-07 07:38:09.008877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52b6a1b5166e'
down_revision = '848b1a80cc28'
branch_labels = None
depends_on = None


def upgrade():
    # Create magic_link_token table for passwordless authentication
    op.create_table(
        'magic_link_token',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes for efficient lookups
    op.create_index('ix_magic_link_token_email', 'magic_link_token', ['email'], unique=False)
    op.create_index('ix_magic_link_token_token', 'magic_link_token', ['token'], unique=True)


def downgrade():
    op.drop_index('ix_magic_link_token_token', table_name='magic_link_token')
    op.drop_index('ix_magic_link_token_email', table_name='magic_link_token')
    op.drop_table('magic_link_token')
