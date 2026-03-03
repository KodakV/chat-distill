from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **params: Any,
    ) -> Any:
        ...
