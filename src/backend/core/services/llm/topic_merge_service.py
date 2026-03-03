import json
import logging
from typing import List

from pydantic import ValidationError

from backend.db.models.messages import Messages
from backend.db.models.topics import Topics
from backend.schemas.dto.topic_merge_result import TopicMergeResult
from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner

logger = logging.getLogger(__name__)


class TopicMergeService:
    PARAMS = {
        "temperature": 0.1,
        "max_tokens": 100,
    }

    def __init__(self, runner: LLMRunner) -> None:
        self.runner = runner

    async def should_merge(
        self,
        topic_a: Topics,
        messages_a: List[Messages],
        topic_b: Topics,
        messages_b: List[Messages],
    ) -> TopicMergeResult:

        messages = self._build_messages(topic_a, messages_a, topic_b, messages_b)
        logger.info(
            "[MERGE] LLM check topic_a=%s topic_b=%s",
            topic_a.id,
            topic_b.id,
        )

        res = await self.runner.run(messages=messages, **self.PARAMS)
        logger.info("[MERGE] LLM raw response: %s", res.content)

        try:
            parsed = json.loads(res.content)
            result = TopicMergeResult.model_validate(parsed)
            return result

        except json.JSONDecodeError:
            logger.error("[MERGE] Invalid JSON from LLM: %s", res.content)
            raise ValueError("LLM returned invalid JSON")

        except ValidationError as e:
            logger.error("[MERGE] LLM response validation failed: %s", res.content)
            raise ValueError("LLM returned invalid schema") from e

    def _build_messages(
        self,
        topic_a: Topics,
        messages_a: List[Messages],
        topic_b: Topics,
        messages_b: List[Messages],
    ) -> list[dict]:

        payload = {
            "topic_a": {
                "id": topic_a.id,
                "title": topic_a.title,
                "summary": topic_a.summary,
                "messages": self._render_messages(messages_a),
            },
            "topic_b": {
                "id": topic_b.id,
                "title": topic_b.title,
                "summary": topic_b.summary,
                "messages": self._render_messages(messages_b),
            },
        }

        return [
            {"role": "system", "content": get_prompt("topic_merge")},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

    def _render_messages(self, messages: List[Messages]) -> List[str]:
        result = []
        for m in messages:
            text = (m.text or m.caption or "").strip()
            if not text:
                continue
            author = f"@{m.username}" if m.username else str(m.user_id or "unknown")
            result.append(f"{author}: {text}")
        return result
