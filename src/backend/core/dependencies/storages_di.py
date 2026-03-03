from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_async_db
from backend.db.storages.async_chat_storage import AsyncChatStorage
from backend.db.storages.async_message_storage import AsyncMessageStorage
from backend.db.storages.async_topic_message_storage import AsyncTopicMessageStorage
from backend.db.storages.async_topic_storage import AsyncTopicStorage
from backend.db.storages.async_user_chat_storage import AsyncUserChatStorage
from backend.db.storages.async_user_storage import AsyncUserStorage


def get_async_chat_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncChatStorage:
    return AsyncChatStorage(db)


def get_async_user_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncUserStorage:
    return AsyncUserStorage(db)


def get_async_user_chat_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncUserChatStorage:
    return AsyncUserChatStorage(db)


def get_async_message_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncMessageStorage:
    return AsyncMessageStorage(db)


def get_async_topic_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncTopicStorage:
    return AsyncTopicStorage(db)


def get_async_topic_message_storage(db: AsyncSession = Depends(get_async_db)) -> AsyncTopicMessageStorage:
    return AsyncTopicMessageStorage(db)
