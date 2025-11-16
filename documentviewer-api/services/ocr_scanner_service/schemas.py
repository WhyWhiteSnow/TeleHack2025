from typing import Literal, Optional

from pydantic import BaseModel


class QCRScannerServiceResponse(BaseModel):
    status: Literal["success", "error"]
    data: dict
    tables: list
    message: Optional[str] = None

    class Config:
        from_attributes = True
