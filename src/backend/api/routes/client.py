import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from backend.core.dependencies.storages_di import (
    get_async_message_storage,
    get_async_topic_message_storage,
    get_async_topic_storage,
    get_async_user_chat_storage,
)
from backend.core.dependencies.telegram_auth import WebAppUser, get_webapp_user
from backend.db.storages.async_message_storage import AsyncMessageStorage
from backend.db.storages.async_topic_message_storage import AsyncTopicMessageStorage
from backend.db.storages.async_topic_storage import AsyncTopicStorage
from backend.db.storages.async_user_chat_storage import AsyncUserChatStorage
from backend.schemas.api.client import (
    ChatInfoResponse,
    ChatThreadsResponse,
    ThreadInfoResponse,
    UserChatsResponse,
)
from backend.schemas.api.topics import TopicMessageResponse, TopicWithMessagesResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chats", response_model=UserChatsResponse)
async def get_user_chats(
    current_user: WebAppUser = Depends(get_webapp_user),
    user_chat_storage: AsyncUserChatStorage = Depends(get_async_user_chat_storage),
):
    chats = await user_chat_storage.get_chats_for_user(current_user.id)
    return UserChatsResponse(
        chats=[
            ChatInfoResponse(
                chat_id=c.id,
                title=c.title,
                type=c.type,
                is_forum=c.is_forum,
            )
            for c in chats
        ]
    )


@router.get("/chats/{chat_id}/threads", response_model=ChatThreadsResponse)
async def get_chat_threads(
    chat_id: int,
    current_user: WebAppUser = Depends(get_webapp_user),
    message_storage: AsyncMessageStorage = Depends(get_async_message_storage),
):
    rows = await message_storage.get_threads_for_chat(chat_id)
    threads = [
        ThreadInfoResponse(
            message_thread_id=row.message_thread_id,
            thread_name=row.thread_name,
            message_count=row.message_count,
            last_message_date=row.last_message_date,
        )
        for row in rows
    ]
    return ChatThreadsResponse(chat_id=chat_id, threads=threads)


@router.get("/chats/{chat_id}/topics", response_model=List[TopicWithMessagesResponse])
async def get_chat_topics(
    chat_id: int,
    message_thread_id: Optional[int] = Query(None, description="Filter by thread ID"),
    current_user: WebAppUser = Depends(get_webapp_user),
    topic_storage: AsyncTopicStorage = Depends(get_async_topic_storage),
    topic_message_storage: AsyncTopicMessageStorage = Depends(get_async_topic_message_storage),
):
    topics = await topic_storage.get_active_topics(chat_id, message_thread_id)
    logger.info("topics for chat %s thread %s: %s", chat_id, message_thread_id, topics)

    result = []
    for topic in topics:
        messages = await topic_message_storage.get_messages_for_topic(topic.id)
        message_items = [
            TopicMessageResponse(
                username=m.username,
                text=(m.text or m.caption or "").strip(),
            )
            for m in messages
            if (m.text or m.caption or "").strip()
        ]
        result.append(
            TopicWithMessagesResponse(
                topic_id=topic.id,
                title=topic.title,
                summary=topic.summary,
                messages=message_items,
            )
        )

    return result
