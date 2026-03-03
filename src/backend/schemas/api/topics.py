from typing import List, Optional

from pydantic import BaseModel


class TopicMessageResponse(BaseModel):
    username: Optional[str]
    text: str


class TopicWithMessagesResponse(BaseModel):
    topic_id: int
    title: str
    summary: Optional[str]
    messages: List[TopicMessageResponse]
