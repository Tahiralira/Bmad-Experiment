"""add_expense_and_expense_split

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f9a0b1c2d3'
down_revision = 'd7e8f9a0b1c2'
branch_labels = None
depends_on = None


def upgrade():
    # Create expense table
    op.create_table(
        'expense',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('payer_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['expense_group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payer_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expense_group_id', 'expense', ['group_id'])
    op.create_index('ix_expense_payer_id', 'expense', ['payer_id'])

    # Create expense_split table
    op.create_table(
        'expense_split',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('expense_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount_owed', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['expense_id'], ['expense.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expense_split_expense_id', 'expense_split', ['expense_id'])
    op.create_index('ix_expense_split_user_id', 'expense_split', ['user_id'])


def downgrade():
    op.drop_index('ix_expense_split_user_id', table_name='expense_split')
    op.drop_index('ix_expense_split_expense_id', table_name='expense_split')
    op.drop_table('expense_split')
    op.drop_index('ix_expense_payer_id', table_name='expense')
    op.drop_index('ix_expense_group_id', table_name='expense')
    op.drop_table('expense')
