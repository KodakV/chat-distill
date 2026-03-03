from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.bot_settings import get_bot_settings
from bot.handlers import private, groups
from bot.utils.logging import logger


def create_bot() -> Bot:
    settings = get_bot_settings()
    logger.info("Creating bot")

    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.include_router(private.router)
    dp.include_router(groups.router)

    return dp