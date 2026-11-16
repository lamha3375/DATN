from pydantic import BaseModel
from typing import List


class PageContent(BaseModel):
    page_number: int
    content: str
    character_count: int


class DocumentExtractionResponse(BaseModel):
    filename: str
    total_pages: int
    extracted_pages: int
    empty_pages: List[int]
    total_characters: int
    pages: List[PageContent]