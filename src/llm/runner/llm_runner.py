import logging
from typing import Optional

from llm.clients.llm_client import LLMClient
from llm.results.base import LLMResult

logger = logging.getLogger(__name__)


class LLMRunner:
    def __init__(self, client: LLMClient):
        self.client = client

    async def run(
        self,
        messages: list[dict],
        grammar: Optional[str] = None,
        **params,
    ) -> LLMResult:
        filtered = {k: v for k, v in params.items() if k in self.client.ALLOWED_PARAMS}

        if grammar:
            raw = await self.client.chat(messages=messages, grammar=grammar, **filtered)
        else:
            raw = await self.client.chat(messages=messages, **filtered)

        return LLMResult(
            raw=raw.model_dump(),
            content=raw.choices[0].message.content,
            tokens=raw.usage.total_tokens if raw.usage else None,
        )
