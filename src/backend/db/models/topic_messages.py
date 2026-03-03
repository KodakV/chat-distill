from backend.db.base import Base
from sqlalchemy import BigInteger, Column, DateTime, Float, Index, ForeignKey


class TopicMessages(Base):
    __tablename__ = "topic_message"

    chat_id = Column(BigInteger, primary_key=True)

    topic_id = Column(BigInteger, primary_key=True)

    message_id = Column(
        BigInteger,
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_at = Column(DateTime)
    similarity_score = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_topic", "topic_id"),
        Index("idx_topic_message_chat", "chat_id", "topic_id"),
    )