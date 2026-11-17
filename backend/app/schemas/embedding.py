
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class EmbeddingItem(BaseModel):
    """Vector embedding tương ứng với một chunk."""

    model_config = ConfigDict(
        validate_assignment=True,
    )

    chunk_id: str = Field(..., min_length=1)

    document_id: str = Field(..., min_length=1)

    document_name: str = Field(..., min_length=1)

    page_number: int = Field(..., ge=1)

    chunk_index: int = Field(..., ge=1)

    source_id: Optional[str] = None

    content_hash: str = Field(..., min_length=1)

    token_count: int = Field(default=0, ge=0)

    character_count: int = Field(default=0, ge=0)

    content: str = Field(..., min_length=1)

    embedding: List[float] = Field(
        ...,
        min_length=1,
    )

    dimensions: int = Field(
        ...,
        ge=1,
    )


class EmbeddingResponse(BaseModel):
    """Kết quả tạo embedding cho toàn bộ chunks."""

    model_name: str = Field(
        ...,
        min_length=1,
    )

    total_chunks: int = Field(
        ...,
        ge=0,
    )

    dimensions: int = Field(
        ...,
        ge=1,
    )

    embeddings: List[EmbeddingItem] = Field(
        default_factory=list,
    )
