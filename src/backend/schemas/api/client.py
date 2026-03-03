from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatInfoResponse(BaseModel):
    chat_id: int
    title: Optional[str]
    type: str
    is_forum: bool

    class Config:
        from_attributes = True


class ThreadInfoResponse(BaseModel):
    message_thread_id: int
    thread_name: Optional[str]
    message_count: int
    last_message_date: Optional[datetime]


class UserChatsResponse(BaseModel):
    chats: List[ChatInfoResponse]


class ChatThreadsResponse(BaseModel):
    chat_id: int
    threads: List[ThreadInfoResponse]
