import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger
from config import config
from services.upload_file_service import upload_file_service
from services.start_message_service import start_message_service
from services.upload_image_service import upload_image_service

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await start_message_service.start_command(message)


@dp.message(F.document)
async def handle_document(message: Message):
    await upload_file_service.handle_document(message)

@dp.message(F.photo)
async def image_handler(message: types.Message):
    await upload_image_service.handle_image(message)

@dp.message()
async def text_handler(message: types.Message):
    await message.answer(f"Отправьте файл")


async def main():
    logger.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
