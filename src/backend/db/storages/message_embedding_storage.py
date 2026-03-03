from typing import List

from sqlalchemy.orm import Session

from backend.db.models.message_embeddings import MessageEmbeddings


class MessageEmbeddingStorage:
    def __init__(self, db: Session):
        self.db = db

    def create_embedding(
        self,
        chat_id: int,
        message_id: int,
        embedding: List[float],
    ) -> None:
        obj = MessageEmbeddings(
            chat_id=chat_id,
            message_id=message_id,
            embedding=embedding,
        )
        self.db.add(obj)
