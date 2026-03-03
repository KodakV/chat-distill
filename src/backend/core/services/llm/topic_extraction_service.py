from llm.prompts import get_prompt
from llm.runner.llm_runner import LLMRunner



class TopicExtractService:
    PARAMS ={
        "temperature": 0.1,
        "max_tokens": 1000,
    }

    def __init__(self, runner : LLMRunner):
        self.runner = runner

    async def extract(self, text: str) -> str:
        messages = self._build_messages(text)
        res = await self.runner.run(messages=messages, **self.PARAMS)
        return res.content

    def _build_messages(self, text: str) -> list[dict]:
        return [
            {"role": "system", "content": get_prompt("topic_extraction")},
            {"role": "user", "content": text},
        ]
