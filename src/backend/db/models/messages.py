from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from backend.db.base import Base


class Messages(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    message_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)

    chat_name = Column(String, nullable=False)
    chat_type = Column(String, nullable=False)
    is_forum = Column(Boolean, nullable=False, default=False)

    user_id = Column(BigInteger, nullable=True)
    username = Column(String, nullable=True)

    message_thread_id = Column(BigInteger, nullable=True)
    thread_name = Column(String, nullable=True)
    is_topic_message = Column(Boolean, nullable=False, default=False)

    text = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    entities = Column(JSONB, nullable=True)

    reply_to_message = Column(BigInteger, nullable=True)
    reply_to_user_id = Column(BigInteger, nullable=True)
    reply_to_message_thread_id = Column(BigInteger, nullable=True)

    forward_from_user_id = Column(BigInteger, nullable=True)

    date = Column(DateTime, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    has_media = Column(Boolean, nullable=False, default=False)

    raw_payload = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("chat_id", "message_id", name="uq_chat_message"),
        Index("idx_chat_id", "chat_id"),
        Index("idx_thread_id", "message_thread_id"),
        Index("idx_chat_date", "chat_id", "date"),
        Index("idx_user_id", "user_id"),
        Index("idx_reply_to_message", "reply_to_message"),
        Index("idx_reply_to_user_id", "reply_to_user_id"),
    )
