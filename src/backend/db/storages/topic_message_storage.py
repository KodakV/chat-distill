from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from backend.db.models.messages import Messages
from backend.db.models.topic_messages import TopicMessages


class TopicMessageStorage:
    def __init__(self, db: Session):
        self.db = db

    def assign_messages_bulk(
        self,
        chat_id: int,
        topic_id: int,
        message_ids: List[int],
        similarity_score: float | None,
    ) -> None:
        if not message_ids:
            return

        now = datetime.utcnow()
        objects = [
            TopicMessages(
                chat_id=chat_id,
                topic_id=topic_id,
                message_id=message_id,
                similarity_score=similarity_score,
                assigned_at=now,
            )
            for message_id in message_ids
        ]
        self.db.bulk_save_objects(objects)

    def get_messages_for_topic(self, topic_id: int) -> List[Messages]:
        return (
            self.db.query(Messages)
            .join(TopicMessages, TopicMessages.message_id == Messages.id)
            .filter(TopicMessages.topic_id == topic_id)
            .order_by(Messages.id.asc())
            .all()
        )

    def reassign_topic_messages(
        self,
        from_topic_id: int,
        to_topic_id: int,
        chat_id: int,
    ) -> int:
        existing_in_target = (
            self.db.query(TopicMessages.message_id)
            .filter(
                TopicMessages.topic_id == to_topic_id,
                TopicMessages.chat_id == chat_id,
            )
            .subquery()
        )

        self.db.query(TopicMessages).filter(
            TopicMessages.topic_id == from_topic_id,
            TopicMessages.chat_id == chat_id,
            TopicMessages.message_id.in_(existing_in_target),
        ).delete(synchronize_session=False)

        reassigned = (
            self.db.query(TopicMessages)
            .filter(
                TopicMessages.topic_id == from_topic_id,
                TopicMessages.chat_id == chat_id,
            )
            .update({"topic_id": to_topic_id}, synchronize_session=False)
        )

        self.db.flush()
        return reassigned

    def reassign_specific_messages(
        self,
        from_topic_id: int,
        to_topic_id: int,
        chat_id: int,
        message_ids: List[int],
    ) -> int:
        if not message_ids:
            return 0

        reassigned = (
            self.db.query(TopicMessages)
            .filter(
                TopicMessages.topic_id == from_topic_id,
                TopicMessages.chat_id == chat_id,
                TopicMessages.message_id.in_(message_ids),
            )
            .update({"topic_id": to_topic_id}, synchronize_session=False)
        )

        self.db.flush()
        return reassigned
