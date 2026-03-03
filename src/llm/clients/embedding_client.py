import httpx
from typing import List
from config.llm_settings import get_llm_settings

_MAX_CHARS = 2000


class EmbeddingClient:
    def __init__(self):
        settings = get_llm_settings()
        self.base_url = settings.embedding_base_url
        self.model = settings.embedding_model

    async def create_embedding(self, text: str) -> List[float]:
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={
                    "model": self.model,
                    "input": text
                }
            )

        response.raise_for_status()
        data = response.json()

        return data[0]["embedding"][0]