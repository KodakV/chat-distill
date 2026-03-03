from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.topics import Topics


class AsyncTopicStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_topics(
        self,
        chat_id: int,
        message_thread_id: int | None = None,
    ) -> list[Topics]:
        query = (
            select(Topics)
            .where(Topics.chat_id == chat_id)
            .where(Topics.status == "active")
        )
        if message_thread_id is not None:
            query = query.where(Topics.message_thread_id == message_thread_id)
        else:
            query = query.where(Topics.message_thread_id.is_(None))

        result = await self.db.execute(query)
        return list(result.scalars().all())
