from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models.messages import Messages
from backend.schemas.api.messages import MessageCreateRequest


class MessageStorage:
    def __init__(self, db: Session):
        self.db = db

    def create_message(self, data: MessageCreateRequest) -> Messages:
        message_thread_id = data.message_thread_id
        thread_name = data.thread_name
        if data.chat_type == "supergroup" and message_thread_id is None:
            message_thread_id = 0
            thread_name = "General"

        message = Messages(
            message_id=data.message_id,
            chat_id=data.chat_id,
            chat_name=data.chat_name,
            chat_type=data.chat_type,
            is_forum=data.is_forum,
            user_id=data.user_id,
            username=data.username,
            message_thread_id=message_thread_id,
            thread_name=thread_name,
            is_topic_message=data.is_topic_message,
            text=data.text,
            caption=data.caption,
            entities=data.entities,
            date=data.date,
            edited_at=data.edited_at,
            has_media=data.has_media,
            reply_to_message=data.reply_to_message,
            forward_from_user_id=data.forward_from_user_id,
            raw_payload=data.raw_payload,
        )

        self.db.add(message)
        self.db.flush()

        return message

    def get_by_chat_and_message_id(self, chat_id: int, message_id: int) -> Messages | None:
        return (
            self.db.query(Messages)
            .filter(Messages.chat_id == chat_id)
            .filter(Messages.message_id == message_id)
            .first()
        )

    def get_by_chat_and_message_ids(
        self,
        chat_id: int,
        message_ids: list[int],
    ) -> list[Messages]:
        if not message_ids:
            return []

        messages = (
            self.db.query(Messages)
            .filter(Messages.chat_id == chat_id)
            .filter(Messages.message_id.in_(message_ids))
            .all()
        )

        message_map = {m.message_id: m for m in messages}
        return [message_map[mid] for mid in message_ids if mid in message_map]

    def get_threads_for_chat(self, chat_id: int) -> list[tuple]:
        return (
            self.db.query(
                Messages.message_thread_id,
                func.max(Messages.thread_name).label("thread_name"),
                func.count(Messages.id).label("message_count"),
                func.max(Messages.date).label("last_message_date"),
            )
            .filter(Messages.chat_id == chat_id)
            .filter(Messages.message_thread_id.isnot(None))
            .group_by(Messages.message_thread_id)
            .order_by(func.max(Messages.date).desc())
            .all()
        )
