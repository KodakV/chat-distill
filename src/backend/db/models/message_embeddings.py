from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, BigInteger, Index
from backend.db.base import Base

class MessageEmbeddings(Base):
    __tablename__ = "message_embeddings"

    chat_id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, primary_key=True)

    embedding = Column(Vector(768), nullable=False)

    created_at = Column(DateTime)

    __table_args__ = (
        Index(
            "idx_embedding_cosine",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )