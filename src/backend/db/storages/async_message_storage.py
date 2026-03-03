from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.models.messages import Messages
from backend.schemas.api.messages import MessageCreateRequest


class AsyncMessageStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, data: MessageCreateRequest) -> Messages:
        message_thread_id = data.message_thread_id
        thread_name = data.thread_name
        if data.chat_type == "supergroup" and message_thread_id is None:
            message_thread_id = 0
            thread_name = "General"

        if message_thread_id and not thread_name:
            result = await self.db.execute(
                select(Messages.thread_name)
                .where(Messages.chat_id == data.chat_id)
                .where(Messages.message_thread_id == message_thread_id)
                .where(Messages.thread_name.isnot(None))
                .limit(1)
            )
            thread_name = result.scalar_one_or_none()

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
        await self.db.flush()
        return message

    async def get_threads_for_chat(self, chat_id: int) -> list[tuple]:
        result = await self.db.execute(
            select(
                Messages.message_thread_id,
                func.max(Messages.thread_name).label("thread_name"),
                func.count(Messages.id).label("message_count"),
                func.max(Messages.date).label("last_message_date"),
            )
            .where(Messages.chat_id == chat_id)
            .where(Messages.message_thread_id.isnot(None))
            .group_by(Messages.message_thread_id)
            .order_by(func.max(Messages.date).desc())
        )
        return list(result.all())
