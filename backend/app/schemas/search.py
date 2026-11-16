from typing import List
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    distance: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]