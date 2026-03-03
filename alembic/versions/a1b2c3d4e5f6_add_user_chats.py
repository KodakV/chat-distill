"""add user_chats

Revision ID: a1b2c3d4e5f6
Revises: 882f4f94c3b8
Create Date: 2026-02-24 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '882f4f94c3b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_chats',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'chat_id'),
    )
    op.create_index('ix_user_chats_user_id', 'user_chats', ['user_id'])
    op.create_index('ix_user_chats_chat_id', 'user_chats', ['chat_id'])


def downgrade() -> None:
    op.drop_index('ix_user_chats_chat_id', table_name='user_chats')
    op.drop_index('ix_user_chats_user_id', table_name='user_chats')
    op.drop_table('user_chats')
