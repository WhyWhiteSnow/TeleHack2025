from fastapi import FastAPI

from config import config
from routers.files import router as files_router

app = FastAPI(
    title="Document Viewer API",
    description="API for document viewer",
    version=config.VERSION,
    docs_url="/docs",
)

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

@app.post("/upload_image")
async def upload_image():
    return {}