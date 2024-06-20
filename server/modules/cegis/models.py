from pydantic import BaseModel


class OCRRequest(BaseModel):
    images: list[str]


class OCRImageResponse(BaseModel):
    """
    This is the model placeholder for the ocr output of a single image
    """
    text: str

