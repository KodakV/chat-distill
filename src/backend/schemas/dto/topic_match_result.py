from typing import Optional

from pydantic import BaseModel


class TopicMatchResult(BaseModel):
    topic_id: Optional[int]
    is_match: bool
