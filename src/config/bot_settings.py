from functools import lru_cache

from config.base import Settings


class BotSettings(Settings):

    bot_token: str
    backend_base_url: str
    backend_api_key: str


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
