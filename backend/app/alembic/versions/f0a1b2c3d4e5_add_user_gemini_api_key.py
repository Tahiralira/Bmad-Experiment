"""add_user_gemini_api_key

Revision ID: f0a1b2c3d4e5
Revises: e9f0b1c2d3e4
Create Date: 2026-01-20

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f0a1b2c3d4e5"
down_revision = "e9f0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade():
    # Add gemini_api_key_encrypted column to user table
    op.add_column(
        "user",
        sa.Column("gemini_api_key_encrypted", sa.String(length=512), nullable=True)
    )


def downgrade():
    # Remove gemini_api_key_encrypted column from user table
    op.drop_column("user", "gemini_api_key_encrypted")
