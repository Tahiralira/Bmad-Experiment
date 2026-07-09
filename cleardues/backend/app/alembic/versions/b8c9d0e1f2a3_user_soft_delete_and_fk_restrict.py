"""user soft-delete column + RESTRICT financial FKs

WS4/C4: user rows are soft-deleted (anonymized), never hard-deleted, because
expenses, splits and audit entries are records shared with other people.
The ON DELETE CASCADE policies on the financial tables meant a user hard
delete would silently destroy other members' debt records; RESTRICT makes
the database itself refuse — belt and braces under the soft-delete design.

Revision ID: b8c9d0e1f2a3
Revises: a6b7c8d9e0f1
Create Date: 2026-07-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


_FINANCIAL_USER_FKS = [
    # (constraint name, table, column)
    ("expense_payer_id_fkey", "expense", "payer_id"),
    ("expense_created_by_fkey", "expense", "created_by"),
    ("expense_split_user_id_fkey", "expense_split", "user_id"),
]


def upgrade() -> None:
    # Soft-delete marker on user
    op.add_column(
        "user",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Financial rows must survive their users: CASCADE -> RESTRICT
    for name, table, column in _FINANCIAL_USER_FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name, table, "user", [column], ["id"], ondelete="RESTRICT"
        )


def downgrade() -> None:
    for name, table, column in _FINANCIAL_USER_FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name, table, "user", [column], ["id"], ondelete="CASCADE"
        )

    op.drop_column("user", "deleted_at")
