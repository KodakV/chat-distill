from typing import List
from abc import ABC, abstractmethod


class BaseEmbeddingClient(ABC):

    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        """Return embedding vector for single text"""
        ...