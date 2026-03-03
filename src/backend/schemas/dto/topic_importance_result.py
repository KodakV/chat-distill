from pydantic import BaseModel, field_validator


class TopicImportanceResult(BaseModel):
    importance: int

    @field_validator("importance")
    @classmethod
    def clamp(cls, v: int) -> int:
        return max(1, min(10, v))
