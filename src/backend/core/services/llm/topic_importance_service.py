import json
import logging

from pydantic import ValidationError

from backend.schemas.dto.topic_importance_result import TopicImportanceResult
from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner

logger = logging.getLogger(__name__)


class TopicImportanceService:
    PARAMS = {
        "temperature": 0.1,
        "max_tokens": 50,
    }

    def __init__(self, runner: LLMRunner) -> None:
        self.runner = runner

    async def evaluate(self, text: str) -> int:
        messages = [
            {"role": "system", "content": get_prompt("topic_importance")},
            {"role": "user", "content": text},
        ]

        res = await self.runner.run(messages=messages, **self.PARAMS)
        logger.info("[IMPORTANCE] LLM raw response: %s", res.content)

        try:
            parsed = json.loads(res.content)
            result = TopicImportanceResult.model_validate(parsed)
            return result.importance
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error("[IMPORTANCE] Failed to parse response: %s | error: %s", res.content, e)
            return 10
