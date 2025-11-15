from aiogram.types import Message
import aiohttp
from loguru import logger
from config import config


class UploadImageService:
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def handle_image(self, message: Message):
        try:
            if not message.photo:
                await message.answer("❌ Пожалуйста, отправьте изображение как фото")
                return

            photo = message.photo[-1]
            user_id = message.from_user.id

            processing_msg = await message.answer(
                "📥 Получил изображение. Загружаю на сервер..."
            )

            file_info = await message.bot.get_file(photo.file_id)
            file_path = file_info.file_path
            downloaded_file = await message.bot.download_file(file_path)
            
            filename = f"photo_{user_id}_{photo.file_id}.jpg"

            server_response = await self.send_image_to_server(
                downloaded_file,
                user_id,
                filename,
            )

            response_text = self.format_server_response(server_response)
            await processing_msg.edit_text(f"✅ Изображение обработано!\n\n{response_text}")

        except Exception as e:
            logger.error(f"Error sending image to server: {e}")
            await message.answer(f"❌ Произошла ошибка при обработке изображения: {str(e)}")

    async def send_image_to_server(
        self, file_bytes: bytes, user_id: int, filename: str
    ) -> dict:
        try:         
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file",
                    file_bytes,
                    filename=filename,
                    content_type="image/jpeg",
                )
                form_data.add_field("user_id", str(user_id))
                form_data.add_field("filename", filename)

                async with session.post(
                    f"{self.server_url}/upload_photo",
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
            logger.error(f"Error sending image to server: {e}")
            return {"error": f"Connection error: {str(e)}"}

    def format_server_response(self, response: dict) -> str:
        if "error" in response:
            return f"❌ Ошибка сервера:\n{response.get('message', 'Unknown error')}"

        result = "📊 Результат обработки изображения:\n"

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

upload_image_service = UploadImageService(config.SERVER_URL)