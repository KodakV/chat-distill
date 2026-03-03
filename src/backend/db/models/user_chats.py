from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey

from backend.db.base import Base


class UserChats(Base):
    __tablename__ = "user_chats"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
