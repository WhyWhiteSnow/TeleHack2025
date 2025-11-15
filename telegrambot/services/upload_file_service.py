from aiogram.types import Message
import aiohttp
from loguru import logger
from config import config


class UploadFileService:
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def handle_document(self, message: Message):
        try:
            document = message.document
            user_id = message.from_user.id

            if not document.file_name.lower().endswith('.pdf'):
                await message.answer(
                    "❌ Неверный формат файла!\n"
                    "📄 Пожалуйста, отправьте файл в формате PDF.\n"
                    f"🔍 Ваш файл: {document.file_name}"
                )
                return

            processing_msg = await message.answer(
                f"📥 Получил файл {document.file_name}. Загружаю на сервер..."
            )

            file_info = await message.bot.get_file(document.file_id)
            file_path = file_info.file_path
            downloaded_file = await message.bot.download_file(file_path)

            server_response = await self.send_file_to_server(
                downloaded_file,
                user_id,
                document.file_name,
            )

            response_text = self.format_server_response(server_response)
            await processing_msg.edit_text(f"✅ Файл {document.file_name} обработан!\n\n{response_text}")

        except Exception as e:
            logger.error(f"Error sending file to server: {e}")
            return {"error": f"Connection error: {str(e)}"}

    async def send_file_to_server(
        self, file_bytes: bytes, user_id: int, filename: str
    ) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file",
                    file_bytes,
                    filename=filename,
                    content_type="application/octet-stream",
                )
                form_data.add_field("user_id", str(user_id))
                form_data.add_field("filename", filename)

                async with session.post(
                    f"{self.server_url}/upload",
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
            print(response)
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


upload_file_service = UploadFileService(config.SERVER_URL)
