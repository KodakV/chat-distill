from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.chats import Chats
from backend.db.models.user_chats import UserChats


class AsyncUserChatStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_user_to_chat(self, user_id: int, chat_id: int) -> None:
        result = await self.db.execute(
            select(UserChats).where(
                UserChats.user_id == user_id,
                UserChats.chat_id == chat_id,
            )
        )
        if not result.scalar_one_or_none():
            self.db.add(UserChats(user_id=user_id, chat_id=chat_id))

    async def get_chats_for_user(self, user_id: int) -> list[Chats]:
        result = await self.db.execute(
            select(Chats)
            .join(UserChats, UserChats.chat_id == Chats.id)
            .where(UserChats.user_id == user_id)
            .where(Chats.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())
