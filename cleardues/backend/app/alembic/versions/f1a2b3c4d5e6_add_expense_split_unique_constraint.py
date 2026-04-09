"""add_expense_split_unique_constraint

Revision ID: f1a2b3c4d5e6
Revises: e9f0b1c2d3e4
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    # Add unique constraint on expense_split (expense_id, user_id)
    op.create_unique_constraint(
        "uq_expense_user_split",
        "expense_split",
        ["expense_id", "user_id"]
    )


def downgrade():
    op.drop_constraint("uq_expense_user_split", "expense_split", type_="unique")
