from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models.chats import Chats


class AsyncChatStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, chat_id: int, title: str | None, type: str) -> Chats:
        result = await self.db.execute(select(Chats).where(Chats.id == chat_id))
        chat = result.scalar_one_or_none()
        if chat:
            if not chat.is_active:
                chat.is_active = True
            return chat

        chat = Chats(id=chat_id, title=title, type=type, is_active=True)
        self.db.add(chat)
        return chat

