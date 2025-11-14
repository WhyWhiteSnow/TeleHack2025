from fastapi import FastAPI, File, Form, HTTPException, status

# from telegrambot.services.upload_file import UploadFile
from services.ocr_scanner_service import OCRScannerService

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "OK"}


@app.post("/upload")
async def upload_file(
    file=File(...), user_id: int = Form(...), filename: str = Form(...)
):
    try:
        # Читаем файл в память как байты
        file_bytes = await file.read()

        print(f"Received file: {filename}")
        print(f"File size: {len(file_bytes)} bytes")
        print(f"User ID: {user_id}")
        result: dict = OCRScannerService.read_file(file_bytes)
        print(result)
        # Здесь ваша логика обработки файла
        # Например, сохранение, анализ и т.д.

        # Пример: сохраняем файл (опционально)
        # async with aiofiles.open(f"uploads/{filename}", "wb") as f:
        #     await f.write(file_bytes)

        return {
            "status": "success",
            "filename": filename,
            "user_id": user_id,
            "file_size": len(file_bytes),
            "message": "File uploaded successfully",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="pichkalev error",
        ) from e
