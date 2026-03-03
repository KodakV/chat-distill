import importlib

from config.llm_settings import get_llm_settings

_VALID_LANGUAGES = {"ru", "en"}


def get_prompt(name: str) -> str:
    lang = get_llm_settings().prompt_language
    if lang not in _VALID_LANGUAGES:
        raise ValueError(f"Unsupported prompt language: {lang!r}. Choose from: {_VALID_LANGUAGES}")
    module = importlib.import_module(f"llm.prompts.{lang}.{name}")
    return module.system_prompt
