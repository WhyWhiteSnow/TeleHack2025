import asyncio
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
        user_id = message.from_user.id
        logger.info(f"Start processing photos from the user {user_id}")

        try:
            if not message.photo:
                error_msg = "Image format not supported"
                logger.warning(f"{error_msg} for user {user_id}")
                await message.answer("❌ Формат изображения не поддерживается")
                return {"error": error_msg}

            photo = message.photo[-1]
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
            error_msg = f"Critical error when processing photos: {str(e)}"
            logger.error(f"{error_msg} for user {user_id}")
            await message.answer("❌ Произошла критическая ошибка при обработке изображения")
            return {"error": error_msg}

    async def handle_document(self, message: Message) -> dict | None:
        user_id = message.from_user.id
        logger.info(f"Start processing document from the user {user_id}")

        try:
            document = message.document

            if not document or not document.file_name:
                error_msg = "The document does not contain a file name"
                logger.warning(f"{error_msg} for user {user_id}")
                await message.answer("❌ Не удалось определить файл")
                return {"error": error_msg}

            file_name = document.file_name

            if not self._is_allowed_filename(file_name):
                error_msg = f"Invalid file format: {file_name}"
                logger.warning(f"{error_msg} for user {user_id}")
                await message.answer(
                    "❌ Неверный формат файла!\n"
                    f"📄 Пожалуйста, отправьте файл в формате {self.allowed_extensions}.\n"
                    f"🔍 Ваш файл: {file_name}"
                )
                return {"error": error_msg}

            return await self._process_and_respond(
                message=message,
                file_id=document.file_id,
                user_id=user_id,
                filename=file_name,
                progress_text=f"📥 Получил файл {file_name}. Загружаю на сервер...",
                success_prefix=f"✅ Файл {file_name} обработан!",
            )

        except Exception as e:
            error_msg = f"Critical error when processing a document: {str(e)}"
            logger.error(f"{error_msg} for user {user_id}")
            await message.answer("❌ Произошла критическая ошибка при обработке файла")
            return {"error": error_msg}

    async def send_file_to_server(self, file_bytes: bytes, user_id: int, filename: str) -> dict:
        try:
            endpoint, content_type = self._choose_endpoint_and_content_type(filename)
            url = f"{self.server_url}{endpoint}"

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

                try:
                    async with session.post(
                        url,
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        response_text = await response.text()
                        logger.debug(f"Server response: status {response.status}")

                        if response.status == 200:
                            try:
                                result = await response.json()
                                logger.debug(f"File {filename} was successfully sent to the server")
                                return result
                            except Exception as e:
                                error_msg = f"Error parsing JSON response: {str(e)}"
                                logger.error(f"{error_msg}")
                                return {"error": error_msg, "response_text": response_text}
                        else:
                            error_msg = f"Server error: {response.status}"
                            logger.error(f"{error_msg} for file {filename}: {response_text}")
                            return {
                                "error": error_msg,
                                "message": response_text,
                                "status_code": response.status,
                            }

                except asyncio.TimeoutError:
                    error_msg = "Timeout when sending a file to the server"
                    logger.error(f"{error_msg} for file {filename}")
                    return {"error": error_msg}
                except aiohttp.ClientError as e:
                    error_msg = f"Connection error: {str(e)}"
                    logger.error(f"{error_msg} for file {filename}")
                    return {"error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error when sending a file: {str(e)}"
            logger.error(f"{error_msg} for file {filename}")
            return {"error": error_msg}

    def format_server_response(self, response: dict) -> str:
        try:
            if "error" in response:
                logger.warning(f"An error response was received: {response['error']}")
                return f"Processing error:\n{response.get('message', response['error'])}"

            result = "📊 Результат обработки:\n"

            if "message" in response:
                result += f"📝 {response['message']}\n"
                logger.info(f"Message from server: {response['message']}")

            if "data" in response:
                data = response["data"]
                if isinstance(data, dict):
                    for key, value in data.items():
                        result += f"• {key}: {value}\n"
                    logger.debug(f"Received data in dict format: {len(data)} keys")
                elif isinstance(data, list):
                    for item in data[:5]:
                        result += f"• {item}\n"
                    if len(data) > 5:
                        result += f"• ... и еще {len(data) - 5} элементов\n"
                    logger.debug(f"Received data in list format: {len(data)} elements")
                else:
                    result += f"• {data}\n"
                    logger.debug(f"Received data: {data}")

            logger.debug("Successful formatting of server response")
            return result

        except Exception as e:
            error_msg = f"Error formatting server response: {str(e)}"
            logger.error(f"{error_msg}, response: {response}")
            return "❌ Произошла ошибка при обработке ответа от сервера"

    async def _process_and_respond(
        self,
        message: Message,
        file_id: str,
        user_id: int,
        filename: str,
        progress_text: str,
        success_prefix: str,
    ) -> dict:
        logger.info(f"Start processing {filename} from the user {user_id}")

        try:
            processing_msg = await message.answer(progress_text)

            file_bytes = await self._download_tg_file(message, file_id)
            server_response = await self.send_file_to_server(
                file_bytes=file_bytes,
                user_id=user_id,
                filename=filename,
            )
            m_size = 4096
            response_text = self.format_server_response(server_response)
            print(response_text)
            text = [response_text[i : i + m_size] for i in range(0, len(response_text), m_size)]
            print(text)
            await processing_msg.answer(f"{success_prefix}")
            for i in range(len(text)):
                await processing_msg.answer(f"{text[i]}")
            return server_response

        except Exception as e:
            error_msg = f"Error during processing {filename}: {str(e)}"
            logger.error(f"{error_msg} for {filename}")

            try:
                await processing_msg.edit_text("An error occurred while processing the file")
            except Exception:
                await message.answer("An error occurred while processing the file")

            return {"error": error_msg}

    async def _download_tg_file(self, message: Message, file_id: str) -> bytes:
        try:
            file_info = await message.bot.get_file(file_id)
            if not file_info:
                logger.error(f"Failed to get file information {file_id}")
                return None

            file_path = file_info.file_path

            file_bytes = await message.bot.download_file(file_path)
            if file_bytes:
                logger.debug(f"File {file_id} uploaded successfully")
            else:
                logger.error(f"Failed to load file {file_id}")

            return file_bytes

        except Exception as e:
            logger.error(f"Error loading file {file_id} from Telegram: {str(e)}")
            return None

    def _is_allowed_filename(self, filename: str) -> bool:
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            is_allowed = file_ext in self.allowed_extensions
            return is_allowed
        except Exception as e:
            logger.error(f"File extension check error{filename}: {str(e)}")
            return False

    def _choose_endpoint_and_content_type(self, filename: str) -> tuple[str, str]:
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext in self.image_extensions:
                return "/upload-image", "image/jpeg"
            else:
                return "/upload", "application/octet-stream"
        except Exception as e:
            logger.error(f"Error selecting endpoint for {filename}: {str(e)}")
            return "/upload", "application/octet-stream"


upload_file_service = UploadFileService(config.SERVER_URL)
