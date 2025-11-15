from fastapi import FastAPI, File, Form, HTTPException, status
from services.ocr_scanner_service import ocr_scanner_service

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "OK"}


@app.post("/upload")
async def upload_file(
    file=File(...), user_id: int = Form(...), filename: str = Form(...)
):
    try:
        file_bytes = await file.read()

        print(f"Received file: {filename}")
        print(f"File size: {len(file_bytes)} bytes")
        print(f"User ID: {user_id}")
        result: dict = ocr_scanner_service.process_pdf(pdf_bytes=file_bytes)
        print(result)

        return {
            "status": "success",
            "filename": filename,
            "user_id": user_id,
            "file_size": len(file_bytes),
            "message": "Файл успешно обработан",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="server error",
        ) from e
