from dataclasses import dataclass


@dataclass
class LLMResult:
    raw: dict
    content: str
    tokens : int
