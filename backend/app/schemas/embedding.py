from typing import List

from pydantic import BaseModel, Field


class EmbeddingItem(BaseModel):
    chunk_id: str = Field(..., min_length=1)

    document_name: str = Field(..., min_length=1)
    page_number: int = Field(..., ge=1)
    chunk_index: int = Field(..., ge=1)

    content: str = Field(..., min_length=1)

    embedding: List[float]
    dimensions: int = Field(..., gt=0)


class EmbeddingResponse(BaseModel):
    model_name: str
    total_chunks: int = Field(..., ge=0)
    dimensions: int = Field(..., gt=0)

    embeddings: List[EmbeddingItem]