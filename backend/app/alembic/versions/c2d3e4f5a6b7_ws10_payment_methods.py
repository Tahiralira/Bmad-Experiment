"""WS10.2: payment methods registry

- payment_method: per-user GLOBAL payment handles (Venmo, PayPal.Me, Cash App,
  Revolut, UPI, IBAN, custom). Surfaced to a counterparty at settle time so a
  debtor can actually pay. Unique per (user, provider, handle); cascades with
  the user (hard delete) and is scrubbed on soft-delete.

Revision ID: c2d3e4f5a6b7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_method",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "handle",
            name="uq_payment_method_user_provider_handle",
        ),
    )
    op.create_index(
        "ix_payment_method_user_id", "payment_method", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_payment_method_user_id", table_name="payment_method")
    op.drop_table("payment_method")
