from llm.clients.embedding_client import EmbeddingClient
from llm.runner.embedding_runner import EmbeddingRunner
from typing import List


class EmbeddingService:
    def __init__(self, runner: EmbeddingRunner):
        self.runner = runner

    async def generate_embedding(self, text: str) -> List[float]:
        return await self.runner.create_embedding(text)
