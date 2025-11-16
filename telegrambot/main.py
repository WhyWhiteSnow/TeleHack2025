import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger
from config import config
from services.upload_file_service import upload_file_service

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "Привет! Я бот для работы с файлами.\n\n"
        "Отправьте мне pdf файл, и я:\n"
        "1. Загружу его на сервер\n"
        "2. Получу ответ от сервера\n"
        "3. Отправлю вам результат\n\n"
        "Просто отправьте файл и ждите ответ!"
    )
    await message.answer(welcome_text)


@dp.message(F.document)
async def handle_document(message: Message):
    await upload_file_service.handle_document(message)

@dp.message(F.photo)
async def image_handler(message: types.Message):
    await upload_file_service.handle_photo(message)


@dp.message()
async def text_handler(message: types.Message):
    await message.answer(f"Отправьте файл")


async def main():
    logger.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
