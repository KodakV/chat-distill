from typing import List
from pydantic import BaseModel


class TopicSplitResult(BaseModel):
    should_split: bool
    groups: List[List[int]] | None = None
