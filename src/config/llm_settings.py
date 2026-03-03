from config.base import Settings
from functools import lru_cache


class LLMSettings(Settings):

    local_llm_base_url: str
    local_llm_api_key: str
    local_llm_model: str

    embedding_base_url: str
    embedding_api_key: str
    embedding_model: str

    prompt_language: str = "ru"


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()
