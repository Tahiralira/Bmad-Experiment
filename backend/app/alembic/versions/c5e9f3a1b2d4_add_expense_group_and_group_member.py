"""add_expense_group_and_group_member

Revision ID: c5e9f3a1b2d4
Revises: b4d8e2f5a6c9
Create Date: 2026-01-08 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c5e9f3a1b2d4"
down_revision = "b4d8e2f5a6c9"
branch_labels = None
depends_on = None


def upgrade():
    # Create expense_group table
    op.create_table(
        "expense_group",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expense_group_name", "expense_group", ["name"])

    # Create group_member table
    op.create_table(
        "group_member",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["expense_group.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_member_group_id", "group_member", ["group_id"])
    op.create_index("ix_group_member_user_id", "group_member", ["user_id"])
    # Unique constraint to prevent duplicate memberships
    op.create_unique_constraint(
        "uq_group_member_group_user", "group_member", ["group_id", "user_id"]
    )


def downgrade():
    op.drop_constraint("uq_group_member_group_user", "group_member", type_="unique")
    op.drop_index("ix_group_member_user_id", "group_member")
    op.drop_index("ix_group_member_group_id", "group_member")
    op.drop_table("group_member")
    op.drop_index("ix_expense_group_name", "expense_group")
    op.drop_table("expense_group")
