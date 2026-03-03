import asyncio

from aiogram import F, Router
from aiogram.types import Message

from bot.clients.backend import BackendClient
from bot.mappers.message_mapper import MessageMapper
from bot.utils.logging import logger

router = Router()

mapper = MessageMapper()
backend_client = BackendClient()

_topic_cache: dict[tuple[int, int], str] = {}


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    ~F.from_user.is_bot
)
async def handle_group_messages(message: Message):

    chat_id = message.chat.id

    if message.forum_topic_created:
        name = message.forum_topic_created.name
        _topic_cache[(chat_id, message.message_id)] = name
        if message.message_thread_id:
            _topic_cache[(chat_id, message.message_thread_id)] = name

    if message.forum_topic_edited and message.forum_topic_edited.name and message.message_thread_id:
        _topic_cache[(chat_id, message.message_thread_id)] = message.forum_topic_edited.name

    if not (message.text or message.caption or message.photo or message.video
            or message.forum_topic_created or message.forum_topic_edited):
        return

    logger.info(
        "MESSAGE | chat_id=%s | thread_id=%s | user=%s | text=%s",
        chat_id,
        message.message_thread_id,
        message.from_user.username if message.from_user else None,
        (message.text or message.caption or "")[:150],
    )

    try:
        payload = mapper.to_dto(message)
    except Exception as e:
        logger.exception("Failed to map message: %s", e)
        return

    if payload.thread_name is None and message.message_thread_id:
        cached = _topic_cache.get((chat_id, message.message_thread_id))
        if cached:
            payload.thread_name = cached
            logger.debug("MESSAGE | thread_name resolved from cache: %s", cached)

    async def send_to_backend():
        try:
            await backend_client.save_message(payload)
        except Exception as e:
            logger.exception("Backend save failed: %s", e)

    asyncio.create_task(send_to_backend())
