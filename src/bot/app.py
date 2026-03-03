import asyncio

from bot.clients.telegram import create_bot, create_dispatcher
from bot.utils.logging import logger


async def main():
    logger.info("Starting bot")

    bot = create_bot()
    dp = create_dispatcher()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())