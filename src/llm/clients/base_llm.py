from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLMClient(ABC):

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **params: Any,
    ) -> Any:
        ...
