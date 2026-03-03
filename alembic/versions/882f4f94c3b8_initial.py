"""initial

Revision ID: 882f4f94c3b8
Revises:
Create Date: 2026-02-22 07:41:56.530395
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision: str = '882f4f94c3b8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'chats',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('is_forum', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'message_embeddings',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('chat_id', 'message_id')
    )

    op.create_index(
        'idx_embedding_cosine',
        'message_embeddings',
        ['embedding'],
        unique=False,
        postgresql_using='ivfflat',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_name', sa.String(), nullable=False),
        sa.Column('chat_type', sa.String(), nullable=False),
        sa.Column('is_forum', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('message_thread_id', sa.BigInteger(), nullable=True),
        sa.Column('thread_name', sa.String(), nullable=True),
        sa.Column('is_topic_message', sa.Boolean(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reply_to_message', sa.BigInteger(), nullable=True),
        sa.Column('reply_to_user_id', sa.BigInteger(), nullable=True),
        sa.Column('reply_to_message_thread_id', sa.BigInteger(), nullable=True),
        sa.Column('forward_from_user_id', sa.BigInteger(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('has_media', sa.Boolean(), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id', 'message_id', name='uq_chat_message')
    )

    op.create_index('idx_chat_date', 'messages', ['chat_id', 'date'])
    op.create_index('idx_chat_id', 'messages', ['chat_id'])
    op.create_index('idx_reply_to_message', 'messages', ['reply_to_message'])
    op.create_index('idx_reply_to_user_id', 'messages', ['reply_to_user_id'])
    op.create_index('idx_thread_id', 'messages', ['message_thread_id'])
    op.create_index('idx_user_id', 'messages', ['user_id'])

    op.create_table(
        'topic',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message_thread_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('embeddings', Vector(768), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_topic_chat', 'topic', ['chat_id'])
    op.create_index('idx_topic_chat_thread', 'topic', ['chat_id', 'message_thread_id'])

    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'chat_buffer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message_thread_id', sa.BigInteger(), nullable=True),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('locked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['chat_id', 'message_id'],
            ['messages.chat_id', 'messages.message_id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_chat_buffer_chat_id', 'chat_buffer', ['chat_id'])
    op.create_index('ix_chat_buffer_chat_locked', 'chat_buffer', ['chat_id', 'locked'])
    op.create_index('ix_chat_buffer_chat_processed', 'chat_buffer', ['chat_id', 'processed'])
    op.create_index('ix_chat_buffer_created_at', 'chat_buffer', ['created_at'])
    op.create_index('ix_chat_buffer_locked', 'chat_buffer', ['locked'])
    op.create_index('ix_chat_buffer_message_thread', 'chat_buffer', ['chat_id', 'message_thread_id'])
    op.create_index('ix_chat_buffer_message_thread_id', 'chat_buffer', ['message_thread_id'])
    op.create_index('ix_chat_buffer_processed', 'chat_buffer', ['processed'])

    op.create_table(
        'topic_message',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chat_id', 'topic_id', 'message_id')
    )

    op.create_index('idx_topic', 'topic_message', ['topic_id'])
    op.create_index('idx_topic_message_chat', 'topic_message', ['chat_id', 'topic_id'])


def downgrade() -> None:
    op.drop_index('idx_topic_message_chat', table_name='topic_message')
    op.drop_index('idx_topic', table_name='topic_message')
    op.drop_table('topic_message')

    op.drop_table('chat_buffer')
    op.drop_table('users')
    op.drop_table('topic')
    op.drop_table('messages')
    op.drop_table('message_embeddings')
    op.drop_table('chats')