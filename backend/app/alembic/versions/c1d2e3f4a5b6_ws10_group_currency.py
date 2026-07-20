"""WS10.1: per-group currency

- group_settings.currency: ISO-4217 code, default 'USD'. ClearDues is a global
  product — currency is a per-group setting, never hardcoded to one market.
  Existing rows backfill to 'USD' via the server_default.

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-07-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "group_settings",
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default="USD",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("group_settings", "currency")
