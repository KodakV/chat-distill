from backend.db.base import Base
from sqlalchemy import Column, BigInteger, String


class Users(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
