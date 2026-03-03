from sqlalchemy import BigInteger, Column, String

from backend.db.base import Base


class Users(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
