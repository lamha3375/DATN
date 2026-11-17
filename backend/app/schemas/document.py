
#Schema kết quả trích xuất PDF
from typing import List
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    page_number: int = Field(..., ge=1)
    content: str
    character_count: int = Field(..., ge=0)


class DocumentExtractionResponse(BaseModel):
    filename: str
    total_pages: int = Field(..., ge=0)
    extracted_pages: int = Field(..., ge=0)
    empty_pages: List[int] = Field(default_factory=list)
    total_characters: int = Field(..., ge=0)
    pages: List[PageContent] = Field(default_factory=list)