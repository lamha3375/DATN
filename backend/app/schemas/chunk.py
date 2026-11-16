from typing import List

from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    chunk_id: str = Field(..., min_length=1)
    document_name: str = Field(..., min_length=1)
    page_number: int = Field(..., ge=1)

    content: str = Field(..., min_length=1)
    character_count: int = Field(..., ge=1)

    chunk_index: int = Field(..., ge=1)


class ChunkingResponse(BaseModel):
    document_name: str = Field(..., min_length=1)

    total_pages: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)

    chunks: List[TextChunk]