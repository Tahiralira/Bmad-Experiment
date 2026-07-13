"""WS6: aggregate settle-up + strict mode

- settlement_claim grows the aggregate shape: expense_split_id becomes
  nullable; group_id + counterparty_user_id added (set only on aggregate
  claims).
- settlement_claim_split: link table recording which confirmed splits an
  aggregate claim covers. Unique on expense_split_id = the concurrency guard
  against two claims covering the same split.
- group_settings.strict_mode: per-group confirmation policy toggle
  (default false = confirmation opt-in, auto-confirm after N days).

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- settlement_claim: aggregate settle-up shape -------------------------
    op.alter_column(
        "settlement_claim",
        "expense_split_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.add_column(
        "settlement_claim", sa.Column("group_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "settlement_claim",
        sa.Column("counterparty_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "settlement_claim_group_id_fkey",
        "settlement_claim",
        "expense_group",
        ["group_id"],
        ["id"],
    )
    op.create_foreign_key(
        "settlement_claim_counterparty_user_id_fkey",
        "settlement_claim",
        "user",
        ["counterparty_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_settlement_claim_group_id", "settlement_claim", ["group_id"]
    )
    op.create_index(
        "ix_settlement_claim_counterparty_user_id",
        "settlement_claim",
        ["counterparty_user_id"],
    )

    # --- settlement_claim_split: covered splits of an aggregate claim --------
    op.create_table(
        "settlement_claim_split",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("expense_split_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["claim_id"], ["settlement_claim.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["expense_split_id"], ["expense_split.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "expense_split_id", name="uq_settlement_claim_split_split"
        ),
    )
    op.create_index(
        "ix_settlement_claim_split_claim_id",
        "settlement_claim_split",
        ["claim_id"],
    )

    # --- group_settings: strict mode toggle ----------------------------------
    op.add_column(
        "group_settings",
        sa.Column(
            "strict_mode",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("group_settings", "strict_mode")

    op.drop_index(
        "ix_settlement_claim_split_claim_id", table_name="settlement_claim_split"
    )
    op.drop_table("settlement_claim_split")

    # Aggregate claims cannot survive a NOT NULL expense_split_id
    op.execute("DELETE FROM settlement_claim WHERE expense_split_id IS NULL")
    op.drop_index(
        "ix_settlement_claim_counterparty_user_id", table_name="settlement_claim"
    )
    op.drop_index("ix_settlement_claim_group_id", table_name="settlement_claim")
    op.drop_constraint(
        "settlement_claim_counterparty_user_id_fkey",
        "settlement_claim",
        type_="foreignkey",
    )
    op.drop_constraint(
        "settlement_claim_group_id_fkey", "settlement_claim", type_="foreignkey"
    )
    op.drop_column("settlement_claim", "counterparty_user_id")
    op.drop_column("settlement_claim", "group_id")
    op.alter_column(
        "settlement_claim",
        "expense_split_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
