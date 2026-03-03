from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text

from backend.db.base import Base


class Topics(Base):
    __tablename__ = "topic"
    id = Column(BigInteger, primary_key=True, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    message_thread_id = Column(BigInteger, nullable=True)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    embeddings = Column(Vector(768), nullable=True)
    message_count = Column(Integer, nullable=True)
    participant_count = Column(Integer, nullable=True)
    status = Column(String, nullable=True)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_topic_chat", "chat_id"),
        Index("idx_topic_chat_thread", "chat_id", "message_thread_id"),
    )
