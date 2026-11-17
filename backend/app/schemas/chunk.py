
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class TextChunk(BaseModel):
    """Một đoạn văn bản được chia từ tài liệu PDF."""

    model_config = ConfigDict(
        str_strip_whitespace=False,
        validate_assignment=True,
    )

    chunk_id: str = Field(
        ...,
        min_length=1,
        description="ID duy nhất của chunk",
    )

    document_id: str = Field(
        ...,
        min_length=1,
        description="ID tài liệu vật lý, liên kết với DocumentFile",
    )

    document_name: str = Field(
        ...,
        min_length=1,
        description="Tên file PDF gốc",
    )

    page_number: int = Field(
        ...,
        ge=1,
        description="Số trang PDF chứa nội dung chunk",
    )

    source_id: Optional[str] = Field(
        default=None,
        description="ID Source trong Neo4j nếu xác định được",
    )

    content_hash: str = Field(
        ...,
        min_length=1,
        description="SHA256 của file PDF gốc",
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Nội dung văn bản của chunk",
    )

    character_count: int = Field(
        ...,
        ge=0,
        description="Số ký tự trong chunk",
    )

    token_count: int = Field(
        ...,
        ge=0,
        description="Số token trong chunk",
    )

    chunk_index: int = Field(
        ...,
        ge=1,
        description="Thứ tự chunk trong tài liệu",
    )


class ChunkingResponse(BaseModel):
    """Kết quả chia tài liệu thành các chunks."""

    document_id: str = Field(
        ...,
        min_length=1,
    )

    document_name: str = Field(
        ...,
        min_length=1,
    )

    content_hash: str = Field(
        ...,
        min_length=1,
    )

    total_chunks: int = Field(
        ...,
        ge=0,
    )

    total_characters: int = Field(
        default=0,
        ge=0,
    )

    total_tokens: int = Field(
        default=0,
        ge=0,
    )

    chunks: List[TextChunk] = Field(
        default_factory=list,
    )
