from datetime import datetime
from typing import Any, Literal, Text

from pydantic import BaseModel


ChatType = Literal["private", "group", "supergroup"]


class MessageBase(BaseModel):

    message_id: int
    text: Text | None
    caption: str | None
    entities: list[dict[str, Any]] | None
    date: datetime
    edited_at: datetime | None
    has_media: bool

    reply_to_message: int | None
    reply_to_user_id: int | None
    reply_to_message_thread_id: int | None
    forward_from_user_id: int | None

    chat_id: int
    chat_name: str
    chat_type: ChatType
    is_forum: bool

    message_thread_id: int | None
    thread_name: str | None
    is_topic_message: bool

    user_id: int | None
    username: str | None

    raw_payload: dict[str, Any]

class MessageCreateRequest(MessageBase):
    pass


class MessageCreateResponse(BaseModel):
    status: Literal["ok", "skipped"]
