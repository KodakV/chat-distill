from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models.topic_messages import TopicMessages
from backend.db.models.messages import Messages


class AsyncTopicMessageStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_messages_for_topic(self, topic_id: int) -> list[Messages]:
        result = await self.db.execute(
            select(Messages)
            .join(TopicMessages, TopicMessages.message_id == Messages.id)
            .where(TopicMessages.topic_id == topic_id)
        )
        return list(result.scalars().all())
