from __future__ import annotations

import logging
from typing import List

from backend.db.models.messages import Messages
from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner

logger = logging.getLogger(__name__)


class SummarizationService:

    PARAMS = {
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    def __init__(self, runner: LLMRunner) -> None:
        self.runner = runner

    async def summarize_messages(self, messages: List[Messages]) -> str:
        if not messages:
            return "Обсуждение отсутствует."

        user_content: str = self._render_messages_for_llm(messages)

        logger.info("summarization_input=%s", user_content)

        llm_messages = [
            {"role": "system", "content": get_prompt("summarization")},
            {"role": "user", "content": user_content},
        ]

        result = await self.runner.run(llm_messages, **self.PARAMS)

        if not result:
            logger.warning("summarization: empty result")
            return ""

        content = (result.content or "").strip()

        logger.info("summarization_output_len=%s", len(content))

        return content

    async def resummarize(self, text: str) -> str:

        llm_messages = [
            {"role": "system", "content": get_prompt("resummarization")},
            {"role": "user", "content": text},
        ]
        summary =  await self.runner.run(llm_messages, **self.PARAMS)
        return summary.content

    async def summarize(self, text: str) -> str:

        llm_messages = [
            {"role": "system", "content": get_prompt("summarization")},
            {"role": "user", "content": text},
        ]
        summary =  await self.runner.run(llm_messages, **self.PARAMS)
        return summary.content

    @staticmethod
    def _extract_forward_author(m: Messages) -> str | None:
        raw = m.raw_payload or {}

        forward_from = raw.get("forward_from")
        if forward_from:
            username = forward_from.get("username")
            if username:
                return f"@{username}"
            first = forward_from.get("first_name") or ""
            last = forward_from.get("last_name") or ""
            full = f"{first} {last}".strip()
            return full or str(forward_from.get("id", "unknown"))

        forward_from_chat = raw.get("forward_from_chat")
        if forward_from_chat:
            username = forward_from_chat.get("username")
            if username:
                return f"@{username}"
            return forward_from_chat.get("title") or "канал"

        sender_name = raw.get("forward_sender_name")
        if sender_name:
            return sender_name

        if m.forward_from_user_id:
            return str(m.forward_from_user_id)

        return None

    def _render_messages_for_llm(self, messages: List[Messages]) -> str:
        lines: list[str] = []
        lines.append("СООБЩЕНИЯ ДЛЯ АНАЛИЗА:\n")

        for m in messages:
            content: str = (m.text or m.caption or "").strip()
            if not content:
                continue

            author: str = f"@{m.username}" if m.username else "неизвестный"
            forward_author = self._extract_forward_author(m)

            if forward_author:
                lines.append(
                    f"{author} переслал сообщение от {forward_author} (текст написан {forward_author}): {content}"
                )
            else:
                lines.append(f"{author}: {content}")

        return "\n".join(lines).strip()