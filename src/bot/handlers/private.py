from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.utils.logging import logger

router = Router(name="private")


@router.message(F.chat.type == "private", CommandStart())
async def start_command(message: Message):
    logger.info(
        "PRIVATE /start | user_id=%s username=%s",
        message.from_user.id if message.from_user else None,
        message.from_user.username if message.from_user else None,
    )

    await message.answer(
        "Бот запущен.\n"
        "Напиши /help чтобы посмотреть доступные команды."
    )


@router.message(F.chat.type == "private", Command("help"))
async def help_command(message: Message):
    logger.info(
        "PRIVATE /help | user_id=%s username=%s",
        message.from_user.id if message.from_user else None,
        message.from_user.username if message.from_user else None,
    )

    await message.answer(
        "Доступные команды:\n"
        "/start — запуск бота\n"
        "/help — помощь\n"
        "/about — о боте"
    )


@router.message(F.chat.type == "private", Command("about"))
async def about_command(message: Message):
    logger.info(
        "PRIVATE /about | user_id=%s username=%s",
        message.from_user.id if message.from_user else None,
        message.from_user.username if message.from_user else None,
    )

    await message.answer(
        "Этот бот собирает сообщения из групп и сохраняет их для анализа."
    )


@router.message(F.chat.type == "private")
async def private_fallback(message: Message):
    logger.info(
        "PRIVATE fallback | user_id=%s username=%s text=%r",
        message.from_user.id if message.from_user else None,
        message.from_user.username if message.from_user else None,
        message.text or message.caption,
    )

    await message.answer(
        "Я понимаю только команды.\n"
        "Попробуй /help"
    )
