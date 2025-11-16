from typing import Literal

from pydantic import BaseModel


class UploadFileResponse(BaseModel):
    status: Literal["success", "error"]
    filename: str
    user_id: int
    file_size: int
    message: str
    data: dict
