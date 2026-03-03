import httpx
from typing import List, Dict, Any
from openai import AsyncOpenAI

from llm.clients.base_llm import BaseLLMClient
from config.llm_settings import get_llm_settings


class LLMClient(BaseLLMClient):
    ALLOWED_PARAMS = {
        "temperature",
        "top_p",
        "top_k",
        "max_tokens",
        "stop",
        "grammar",
    }

    def __init__(self):
        settings = get_llm_settings()
        self.model = settings.local_llm_model
        self.client = AsyncOpenAI(
            base_url=settings.local_llm_base_url,
            api_key=settings.local_llm_api_key,
            timeout=httpx.Timeout(connect=120.0, read=600.0, write=30.0, pool=30.0),
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **params: Any,
    ):
        filtered = {k: v for k, v in params.items() if k in self.ALLOWED_PARAMS}
        try:
            return await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **filtered,
            )
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}") from e
