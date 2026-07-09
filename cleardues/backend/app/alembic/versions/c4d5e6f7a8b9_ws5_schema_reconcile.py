"""WS5 schema reconcile (B-H9): unify timestamp/varchar drift

audit_log and settlement_claim were created with naive DateTime() (plus three
stray columns: expense.confirmed_at, user.created_at/updated_at) while every
other column uses DateTime(timezone=True) — naive vs aware timestamps in the
same schema is a comparison bug waiting to happen. Stored values have always
been UTC wall-clock (the app writes datetime.now(timezone.utc) and the
containers run UTC), so AT TIME ZONE 'UTC' reinterprets them losslessly.

Also pins the two unbounded VARCHARs (settlement_claim.status,
audit_log.action_type) to the same bounded style as every other status
column. Values are enum NAMES (e.g. "PENDING", "SPLIT_UPDATED") — max 20 and
30 chars respectively.

After this migration the models (updated in the same work session) render
exactly the schema the migrations create: `alembic check` is clean and
autogenerate works for every future story.

Revision ID: c4d5e6f7a8b9
Revises: b8c9d0e1f2a3
Create Date: 2026-07-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


_NAIVE_TO_AWARE = [
    # (table, column, nullable)
    ("audit_log", "created_at", False),
    ("settlement_claim", "claimed_at", False),
    ("settlement_claim", "confirmed_at", True),
    ("settlement_claim", "rejected_at", True),
    ("settlement_claim", "created_at", False),
    ("expense", "confirmed_at", True),
    ("user", "created_at", False),
    ("user", "updated_at", False),
]


def upgrade() -> None:
    for table, column, nullable in _NAIVE_TO_AWARE:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )

    op.alter_column(
        "settlement_claim",
        "status",
        existing_type=sa.String(),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_log",
        "action_type",
        existing_type=sa.String(),
        type_=sa.String(length=30),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "audit_log",
        "action_type",
        existing_type=sa.String(length=30),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "settlement_claim",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(),
        existing_nullable=False,
    )

    for table, column, nullable in _NAIVE_TO_AWARE:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
