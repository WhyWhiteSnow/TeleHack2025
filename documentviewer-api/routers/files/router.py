from typing import Annotated

from fastapi import APIRouter, Form, UploadFile

from services.ocr_scanner_service.service import ocr_scanner_service
from services.ocr_image_service import handle_pdf_upload, process_image_all_text
from .schemas import UploadFileResponse

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, Form(...)],
    user_id: int = Form(...),
    filename: str = Form(...),
) -> UploadFileResponse:
    file_bytes = await file.read()
    # with tables
    result = handle_pdf_upload(file_bytes)
    if "error" in result["data"]:
        # only if text-like tpd
        result = ocr_scanner_service.process_pdf(pdf_bytes=file_bytes)
        return UploadFileResponse(
            status=result.status,
            filename=filename,
            user_id=user_id,
            file_size=len(file_bytes),
            message=result.message or "File successfully processed",
            data=result.data,
        )
    # all text
    result2 = process_image_all_text(file_bytes)
    # print(result2)
    result["whole text"] = result2
    print(result)
    return UploadFileResponse(
        status="success",
        filename=filename,
        user_id=user_id,
        file_size=len(file_bytes),
        message="success",
        data=result,
    )


@router.post("/upload-image")
async def upload_image(
    file: Annotated[UploadFile, Form(...)],
    user_id: int = Form(...),
    filename: str = Form(...),
) -> UploadFileResponse:
    # TODO: Implement image upload logic
    return UploadFileResponse(
        status="success",
        filename=filename,
        user_id=user_id,
        file_size=0,
        message="Image successfully processed",
        data={},
    )
