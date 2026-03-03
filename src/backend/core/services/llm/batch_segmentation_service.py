import json
import logging
from typing import List

from llm.runner.llm_runner import LLMRunner
from llm.prompts import get_prompt
from backend.db.models.messages import Messages
from llm.runner.llm_runner import LLMResult

logger = logging.getLogger(__name__)


class BatchSegmentationService:
    PARAMS = {
        "temperature": 0.1,
        "max_tokens": 500,
    }

    def __init__(self, runner: LLMRunner):
        self.runner = runner

    async def segment(self, messages: List[Messages]) -> List[List[int]]:
        prompt_messages = self._build_messages(messages)

        result: LLMResult = await self.runner.run(
            prompt_messages,
            **self.PARAMS
        )

        return self._parse_response(result.content, messages)

    def _build_messages(self, messages: List[Messages]) -> List[dict]:
        formatted = []

        for msg in messages:
            text = msg.text or msg.caption or ""
            formatted.append(f"ID: {msg.id} | {text}")

        joined_text = "\n".join(formatted)

        return [
            {"role": "system", "content": get_prompt("batch_topic_segmenter")},
            {"role": "user", "content": joined_text},
        ]

    def _parse_response(
        self,
        raw_content: str,
        original_messages: List[Messages],
    ) -> List[List[int]]:

        valid_ids = {m.id for m in original_messages}

        try:
            parsed = json.loads(raw_content)
        except Exception:
            logger.error("Failed to parse LLM segmentation response")
            return [[m.id for m in original_messages]]

        if not isinstance(parsed, list):
            return [[m.id for m in original_messages]]

        result: List[List[int]] = []

        for group in parsed:
            if not isinstance(group, list):
                continue

            filtered_ids = [
                msg_id
                for msg_id in group
                if isinstance(msg_id, int) and msg_id in valid_ids
            ]

            if filtered_ids:
                result.append(filtered_ids)

        if not result:
            return [[m.id for m in original_messages]]

        return result