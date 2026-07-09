"""add token revocation (revoked_tokens table + users.refresh_tokens_valid_after)

Revision ID: c9c0e6da1b84
Revises: a183b5a7d554
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9c0e6da1b84'
down_revision: Union[str, Sequence[str], None] = 'a183b5a7d554'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, index: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(table):
        return False
    return any(ix["name"] == index for ix in insp.get_indexes(table))


def upgrade() -> None:
    """Upgrade schema (idempotent — safe to re-run when objects already exist)."""
    if not _has_column('users', 'refresh_tokens_valid_after'):
        op.add_column('users', sa.Column('refresh_tokens_valid_after', sa.DateTime(timezone=True), nullable=True))
    if not _has_table('revoked_tokens'):
        op.create_table('revoked_tokens',
        sa.Column('jti', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('jti')
        )
    if not _has_index('revoked_tokens', op.f('ix_revoked_tokens_user_id')):
        op.create_index(op.f('ix_revoked_tokens_user_id'), 'revoked_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_revoked_tokens_user_id'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
    op.drop_column('users', 'refresh_tokens_valid_after')
