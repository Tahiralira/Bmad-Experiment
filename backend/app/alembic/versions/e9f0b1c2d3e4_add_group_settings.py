"""add_group_settings

Revision ID: e9f0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-01-20

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9f0b1c2d3e4"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    # Create group_settings table
    op.create_table(
        "group_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("ai_personality", sa.String(length=20), nullable=False, server_default="friendly"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["expense_group.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_settings_group_id", "group_settings", ["group_id"], unique=True)
    op.create_index("ix_group_settings_ai_personality", "group_settings", ["ai_personality"])


def downgrade():
    op.drop_index("ix_group_settings_ai_personality", "group_settings")
    op.drop_index("ix_group_settings_group_id", "group_settings")
    op.drop_table("group_settings")
