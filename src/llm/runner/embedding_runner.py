from llm.clients.embedding_client import EmbeddingClient
from typing import List


class EmbeddingRunner:
    def __init__(self, client: EmbeddingClient):
        self.client = client

    async def create_embedding(self, text: str) -> List[float]:
        return await self.client.create_embedding(text)