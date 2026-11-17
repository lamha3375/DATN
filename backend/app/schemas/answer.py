
from typing import List, Optional

from pydantic import BaseModel, Field


class AnswerSource(BaseModel):
    document_name: str
    page_number: Optional[int] = None
    chunk_id: Optional[str] = None
    source_id: Optional[str] = None

class GeneratedAnswer(BaseModel):
    answer: str = Field(
        description="Nội dung trả lời câu hỏi bằng tiếng Việt."
    )
    has_sufficient_context: bool = Field(
        description="Ngữ cảnh có đủ căn cứ để trả lời câu hỏi hay không."
    )


class AnswerResponse(BaseModel):
    query: str
    answer: str
    sources: List[AnswerSource] = Field(default_factory=list)
    has_sufficient_context: bool = False

