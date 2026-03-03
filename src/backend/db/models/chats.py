from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, String

from backend.db.base import Base


class Chats(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)

    title = Column(String, nullable=True)
    type = Column(String, nullable=False)
    is_forum = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)
