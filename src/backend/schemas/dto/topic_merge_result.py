from pydantic import BaseModel


class TopicMergeResult(BaseModel):
    should_merge: bool
