import json
import logging
from typing import List, Union

from pydantic import ValidationError

from backend.db.models.topics import Topics
from backend.schemas.dto.topic_match_result import TopicMatchResult
from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner

logger = logging.getLogger(__name__)


class TopicMatchingService:
    PARAMS = {
        "temperature": 0.1,
        "max_tokens": 100,
    }

    def __init__(self, runner: LLMRunner):
        self.runner = runner

    async def match(
        self,
        text: str,
        topics: Union[
            List[tuple[Topics, float]],
            tuple[Topics, float],
            Topics,
        ],
    ) -> TopicMatchResult:

        if isinstance(topics, Topics):
            topics = [(topics, 1.0)]
        elif isinstance(topics, tuple):
            topics = [topics]

        messages = self._build_messages(text, topics)
        logger.info("topic matching input %s", messages)

        res = await self.runner.run(messages=messages, **self.PARAMS)
        logger.info("raw llm response %s", res.content)

        try:
            parsed = json.loads(res.content)
            result = TopicMatchResult.model_validate(parsed)
            return result

        except json.JSONDecodeError:
            logger.error("Invalid JSON from LLM: %s", res.content)
            raise ValueError("LLM returned invalid JSON")

        except ValidationError as e:
            logger.error("LLM response validation failed: %s", res.content)
            raise ValueError("LLM returned invalid schema") from e

    def _build_messages(
        self,
        text: str,
        topics: List[tuple[Topics, float]],
    ) -> list[dict]:

        topics_data = [
            {
                "id": topic.id,
                "title": topic.title,
                "summary": topic.summary,
                "similarity": round(similarity_score, 3),
            }
            for topic, similarity_score in topics
        ]

        user_payload = {
            "message": text,
            "candidate_topics": topics_data,
        }

        return [
            {"role": "system", "content": get_prompt("topic_matching")},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            },
        ]