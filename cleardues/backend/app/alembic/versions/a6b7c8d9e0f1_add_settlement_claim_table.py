"""add settlement_claim table

Revision ID: a6b7c8d9e0f1
Revises: 5e78d661700e
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a6b7c8d9e0f1"
down_revision = "5e78d661700e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settlement_claim",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_split_id", sa.Uuid(), nullable=False),
        sa.Column("claimant_user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["expense_split_id"], ["expense_split.id"]),
        sa.ForeignKeyConstraint(["claimant_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expense_split_id", name="uq_settlement_claim_split"),
    )
    op.create_index(
        "ix_settlement_claim_expense_split_id",
        "settlement_claim",
        ["expense_split_id"],
        unique=True,
    )
    op.create_index(
        "ix_settlement_claim_claimant_user_id",
        "settlement_claim",
        ["claimant_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_settlement_claim_claimant_user_id", table_name="settlement_claim"
    )
    op.drop_index(
        "ix_settlement_claim_expense_split_id", table_name="settlement_claim"
    )
    op.drop_table("settlement_claim")
