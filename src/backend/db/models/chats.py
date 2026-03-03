
from backend.db.base import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean
from datetime import datetime


class Chats(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)

    title = Column(String, nullable=True)
    type = Column(String, nullable=False)
    is_forum = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)