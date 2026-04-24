from pydantic import BaseModel
from typing import Optional

class OCRResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None

class OCRRequest(BaseModel):
    filename: str
    file_type: str