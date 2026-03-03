from pydantic import BaseModel
from datetime import datetime
from typing import Any, Text, Literal

ChatType = Literal["private", "group", "supergroup", "channel"]

class MessageRequest(BaseModel):
    message_id: int
    chat_id: int
    chat_name: str
    chat_type: ChatType
    is_forum: bool

    user_id: int | None
    username: str | None

    message_thread_id: int | None
    thread_name: str | None
    is_topic_message: bool

    text: Text | None
    caption: str | None
    entities: list[dict[str, Any]] | None

    reply_to_message: int | None = None
    reply_to_message_thread_id: int | None = None
    reply_to_user_id: int | None = None
    is_reply_to_service_message: bool | None = None

    forward_from_user_id: int | None = None

    date: datetime
    edited_at: datetime | None
    has_media: bool

    raw_payload: dict[str, Any]