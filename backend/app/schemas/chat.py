
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.answer import AnswerSource


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Câu hỏi lịch sử của người dùng"
    )

    vector_top_k: int = Field(default=5, ge=1, le=10)
    graph_top_k: int = Field(default=5, ge=1, le=10)


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[AnswerSource] = Field(default_factory=list)
    has_sufficient_context: bool = False
    metadata: dict = Field(default_factory=dict)
