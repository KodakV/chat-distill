from pydantic import BaseModel
from typing import Optional


class TopicMatchResult(BaseModel):
    topic_id: Optional[int]
    is_match: bool