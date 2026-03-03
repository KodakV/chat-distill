from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models.users import Users


class AsyncUserStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: int, username: str | None = None) -> Users:
        result = await self.db.execute(select(Users).where(Users.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

        user = Users(id=user_id, username=username)
        self.db.add(user)
        return user
