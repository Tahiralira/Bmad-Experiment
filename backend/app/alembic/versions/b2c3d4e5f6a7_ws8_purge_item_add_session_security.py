"""WS8: drop template item table; add login_code, revoked_token; cap invites

- Drop `item` — the FastAPI template's demo entity died with the template
  purge (S5-H5/S4-H2). It never held product data.
- `login_code` — single-use short-lived codes for OAuth token delivery
  (S5-H1: the JWT no longer rides the redirect URL).
- `revoked_token` — server-side JWT revocation by jti (S5-H1).
- `group_invite` gains max_uses / use_count / revoked_at (S5-M4: invites
  are capped and revocable).

Revision ID: b2c3d4e5f6a7
Revises: af5ea3c202c0
Create Date: 2026-07-14

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'af5ea3c202c0'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('item')

    op.create_table(
        'login_code',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('code_hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_login_code_code_hash'), 'login_code', ['code_hash'], unique=True)
    op.create_index(op.f('ix_login_code_user_id'), 'login_code', ['user_id'], unique=False)

    op.create_table(
        'revoked_token',
        sa.Column('jti', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('jti'),
    )
    op.create_index(op.f('ix_revoked_token_user_id'), 'revoked_token', ['user_id'], unique=False)

    # Existing invite rows get the new defaults; server_default is dropped
    # right after backfill so the models (plain Python defaults) stay the
    # single source of truth for autogenerate.
    op.add_column(
        'group_invite',
        sa.Column('max_uses', sa.Integer(), nullable=False, server_default='10'),
    )
    op.add_column(
        'group_invite',
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'group_invite',
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column('group_invite', 'max_uses', server_default=None)
    op.alter_column('group_invite', 'use_count', server_default=None)


def downgrade():
    op.drop_column('group_invite', 'revoked_at')
    op.drop_column('group_invite', 'use_count')
    op.drop_column('group_invite', 'max_uses')

    op.drop_index(op.f('ix_revoked_token_user_id'), table_name='revoked_token')
    op.drop_table('revoked_token')

    op.drop_index(op.f('ix_login_code_user_id'), table_name='login_code')
    op.drop_index(op.f('ix_login_code_code_hash'), table_name='login_code')
    op.drop_table('login_code')

    op.create_table(
        'item',
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
