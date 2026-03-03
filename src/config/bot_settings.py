from config.base import Settings
from functools import lru_cache


class BotSettings(Settings):

    bot_token: str
    backend_base_url: str
    backend_api_key: str


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
