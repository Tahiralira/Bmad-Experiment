"""WS13: nudge ladder — level_2_count on nudge_state

Progressive Urgency's top rung needs a counter. Level 3 (social pressure) is
cut from the product, so Level 2 is the last rung — and a last rung that
repeats forever is the nagging ClearDues exists to remove. `level_2_count`
is what lets the engine stop of its own accord after
NUDGE_LEVEL_2_MAX_REMINDERS.

Backfill: existing rows get 0, which is correct rather than merely
convenient. Every row written before this migration was written by the WS12
engine, which only ever sent Level 1 — so no relationship has spent a Level
2 reminder yet, and 0 is the true count, not a default standing in for
unknown history.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default fills existing rows in the same statement; it is then
    # dropped so the column's default lives in the model alone (the WS5/B-H9
    # convention that keeps `alembic check` quiet).
    op.add_column(
        "nudge_state",
        sa.Column(
            "level_2_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("nudge_state", "level_2_count", server_default=None)


def downgrade() -> None:
    op.drop_column("nudge_state", "level_2_count")
