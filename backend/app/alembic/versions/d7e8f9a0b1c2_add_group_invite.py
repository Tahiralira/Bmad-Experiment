"""add_group_invite

Revision ID: d7e8f9a0b1c2
Revises: c5e9f3a1b2d4
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7e8f9a0b1c2'
down_revision = 'c5e9f3a1b2d4'
branch_labels = None
depends_on = None


def upgrade():
    # Create group_invite table
    op.create_table(
        'group_invite',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['expense_group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_invite_token', 'group_invite', ['token'], unique=True)
    op.create_index('ix_group_invite_group_id', 'group_invite', ['group_id'])


def downgrade():
    op.drop_index('ix_group_invite_group_id', table_name='group_invite')
    op.drop_index('ix_group_invite_token', table_name='group_invite')
    op.drop_table('group_invite')
