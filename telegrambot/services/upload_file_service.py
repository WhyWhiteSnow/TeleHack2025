import os

import aiohttp
from aiogram.types import Message
from loguru import logger

from config import config


class UploadFileService:
    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    }
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    def __init__(self, server_url: str):
        self.server_url = server_url

    async def handle_photo(self, message: Message):
        try:
            if not message.photo:
                await message.answer("❌ Пожалуйста, отправьте изображение как фото")
                return

            photo = message.photo[-1]
            user_id = message.from_user.id

            filename = f"photo_{user_id}_{photo.file_id}.jpg"
            return await self._process_and_respond(
                message=message,
                file_id=photo.file_id,
                user_id=user_id,
                filename=filename,
                progress_text="📥 Получил изображение. Загружаю на сервер...",
                success_prefix="✅ Изображение обработано!",
            )

        except Exception as e:
            logger.error(f"Error sending image to server: {e}")
            await message.answer(f"❌ Произошла ошибка при обработке изображения: {str(e)}")
            return {"error": f"Connection error: {str(e)}"}

    async def handle_document(self, message: Message) -> dict | None:
        try:
            document = message.document
            user_id = message.from_user.id

            if not self._is_allowed_filename(document.file_name):
                await message.answer(
                    "❌ Неверный формат файла!\n"
                    f"📄 Пожалуйста, отправьте файл в формате {self.allowed_extensions}.\n"
                    f"🔍 Ваш файл: {document.file_name}"
                )
                return

            return await self._process_and_respond(
                message=message,
                file_id=document.file_id,
                user_id=user_id,
                filename=document.file_name,
                progress_text=f"📥 Получил файл {document.file_name}. Загружаю на сервер...",
                success_prefix=f"✅ Файл {document.file_name} обработан!",
            )

        except Exception as e:
            logger.error(f"Error sending file to server: {e}")
            await message.answer(f"❌ Произошла ошибка при обработке файла: {str(e)}")
            return {"error": f"Connection error: {str(e)}"}

    async def send_file_to_server(self, file_bytes: bytes, user_id: int, filename: str) -> dict:
        try:
            endpoint, content_type = self._choose_endpoint_and_content_type(filename)

            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file",
                    file_bytes,
                    filename=filename,
                    content_type=content_type,
                )
                form_data.add_field("user_id", str(user_id))
                form_data.add_field("filename", filename)

                async with session.post(
                    f"{self.server_url}{endpoint}",
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"Server error: {response.status}",
                            "message": await response.text(),
                        }
        except Exception as e:
            logger.error(f"Error sending file to server: {e}")
            return {"error": f"Connection error: {str(e)}"}

    def format_server_response(self, response: dict) -> str:
        if "error" in response:
            return f"❌ Ошибка сервера:\n{response.get('message', 'Unknown error')}"

        result = "📊 Результат обработки:\n"

        if "message" in response:
            result += f"📝 {response['message']}\n"

        if "data" in response:
            data = response["data"]
            if isinstance(data, dict):
                for key, value in data.items():
                    result += f"• {key}: {value}\n"
            elif isinstance(data, list):
                for item in data[:5]:
                    result += f"• {item}\n"
                if len(data) > 5:
                    result += f"• ... и еще {len(data) - 5} элементов\n"
            else:
                result += f"• {data}\n"

        return result

    async def _process_and_respond(
        self,
        message: Message,
        file_id: str,
        user_id: int,
        filename: str,
        progress_text: str,
        success_prefix: str,
    ) -> dict:
        processing_msg = await message.answer(progress_text)

        file_bytes = await self._download_tg_file(message, file_id)
        server_response = await self.send_file_to_server(
            file_bytes=file_bytes,
            user_id=user_id,
            filename=filename,
        )
        m_size = 4096
        response_text = self.format_server_response(server_response)
        text = [
            response_text[i : i + m_size] for i in range(0, len(response_text) - m_size, m_size)
        ]
        await processing_msg.answer(f"{success_prefix}")
        for i in range(len(text)):
            await processing_msg.answer(f"{text[i]}")
        return server_response

    async def _download_tg_file(self, message: Message, file_id: str) -> bytes:
        file_info = await message.bot.get_file(file_id)
        file_path = file_info.file_path
        return await message.bot.download_file(file_path)

    def _is_allowed_filename(self, filename: str) -> bool:
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in self.allowed_extensions

    def _choose_endpoint_and_content_type(self, filename: str) -> tuple[str, str]:
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext in self.image_extensions:
            return "/upload-image", "image/jpeg"
        return "/upload", "application/octet-stream"


upload_file_service = UploadFileService(config.SERVER_URL)
