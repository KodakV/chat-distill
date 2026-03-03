import json
import logging
from typing import List

from pydantic import ValidationError

from backend.db.models.messages import Messages
from backend.db.models.topics import Topics
from backend.schemas.dto.topic_split_result import TopicSplitResult
from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner

logger = logging.getLogger(__name__)


class TopicSplitService:
    PARAMS = {
        "temperature": 0.1,
        "max_tokens": 500,
    }

    def __init__(self, runner: LLMRunner) -> None:
        self.runner = runner

    async def should_split(
        self,
        topic: Topics,
        messages: List[Messages],
    ) -> TopicSplitResult:

        llm_messages = self._build_messages(topic, messages)
        logger.info(
            "[SPLIT] LLM check topic_id=%s messages=%s",
            topic.id,
            len(messages),
        )

        res = await self.runner.run(messages=llm_messages, **self.PARAMS)
        logger.info("[SPLIT] LLM raw response: %s", res.content)

        try:
            parsed = json.loads(res.content)
            result = TopicSplitResult.model_validate(parsed)
            return result

        except json.JSONDecodeError:
            logger.error("[SPLIT] Invalid JSON from LLM: %s", res.content)
            raise ValueError("LLM returned invalid JSON")

        except ValidationError as e:
            logger.error("[SPLIT] LLM response validation failed: %s", res.content)
            raise ValueError("LLM returned invalid schema") from e

    def _build_messages(
        self,
        topic: Topics,
        messages: List[Messages],
    ) -> list[dict]:

        payload = {
            "topic": {
                "title": topic.title,
                "summary": topic.summary,
            },
            "messages": self._render_messages(messages),
        }

        return [
            {"role": "system", "content": get_prompt("topic_split")},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

    def _render_messages(self, messages: List[Messages]) -> List[dict]:
        result = []
        for idx, m in enumerate(messages, start=1):
            text = (m.text or m.caption or "").strip()
            if not text:
                continue
            author = f"@{m.username}" if m.username else str(m.user_id or "unknown")
            result.append({"index": idx, "author": author, "text": text[:300]})
        return result
