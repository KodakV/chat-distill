from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.api.messages import (
    MessageCreateRequest,
    MessageCreateResponse,
)

from backend.db.session import get_async_db
from backend.db.storages.async_chat_storage import AsyncChatStorage
from backend.db.storages.async_user_storage import AsyncUserStorage
from backend.db.storages.async_user_chat_storage import AsyncUserChatStorage
from backend.db.storages.async_message_storage import AsyncMessageStorage

from backend.core.dependencies.storages_di import (
    get_async_chat_storage,
    get_async_user_storage,
    get_async_user_chat_storage,
    get_async_message_storage,
)

from backend.queue.tasks import process_message_pipeline_task


router = APIRouter()


@router.post("/messages", response_model=MessageCreateResponse)
async def create_message(
    payload: MessageCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    chat_storage: AsyncChatStorage = Depends(get_async_chat_storage),
    message_storage: AsyncMessageStorage = Depends(get_async_message_storage),
    user_storage: AsyncUserStorage = Depends(get_async_user_storage),
    user_chat_storage: AsyncUserChatStorage = Depends(get_async_user_chat_storage),
):
    await chat_storage.get_or_create(
        chat_id=payload.chat_id,
        title=payload.chat_name,
        type=payload.chat_type,
    )

    if payload.user_id is not None:
        await user_storage.get_or_create(
            user_id=payload.user_id,
            username=payload.username,
        )
        await db.flush()
        await user_chat_storage.add_user_to_chat(
            user_id=payload.user_id,
            chat_id=payload.chat_id,
        )

    message = await message_storage.create_message(payload)

    await db.commit()

    process_message_pipeline_task.delay(
        message.chat_id,
        message.message_id,
    )

    return MessageCreateResponse(status="ok")
