from aiogram.types import Message

class StartMessageService:
    async def start_command(self, message: Message):
        welcome_text = (
            "Привет! Я бот для работы с файлами.\n\n"
            "Отправьте мне pdf файл, и я:\n"
            "1. Загружу его на сервер\n"
            "2. Получу ответ от сервера\n"
            "3. Отправлю вам результат\n\n"
            "Просто отправьте файл и ждите ответ!"
        )
        await message.answer(welcome_text)

start_message_service = StartMessageService()