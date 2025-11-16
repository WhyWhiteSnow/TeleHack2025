from typing import Annotated

from fastapi import APIRouter, Form, UploadFile

from services.ocr_scanner_service.service import ocr_scanner_service
from services.ocr_image_service import (
    handle_pdf_upload,
    process_image_all_text,
    process_pic,
    process_image_all_text_for_image,
)
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
    result = ocr_scanner_service.process_pdf(pdf_bytes=file_bytes)
    if result.status == "error":
        print("_________")
        # only if text-like tpd
        result = handle_pdf_upload(file_bytes)
        return UploadFileResponse(
            status="success",
            filename=filename,
            user_id=user_id,
            file_size=len(file_bytes),
            message="success",
            data=result,
        )
    # all text
    result2 = process_image_all_text(file_bytes)
    # print(result2)
    result.data["whole text"] = result2
    print(result)
    return UploadFileResponse(
        status=result.status,
        filename=filename,
        user_id=user_id,
        file_size=len(file_bytes),
        message=result.message or "File successfully processed",
        data=result.data,
    )


@router.post("/upload-image")
async def upload_image(
    file: Annotated[UploadFile, Form(...)],
    user_id: int = Form(...),
    filename: str = Form(...),
) -> UploadFileResponse:
    # TODO: Implement image upload logic
    file_bytes = await file.read()
    result = process_pic(file_bytes)
    result2 = process_image_all_text_for_image(file_bytes)
    result["data"]["whole_text"] = result2
    return UploadFileResponse(
        status="success",
        filename=filename,
        user_id=user_id,
        file_size=len(file_bytes),
        message="Image successfully processed",
        data=result,
    )
