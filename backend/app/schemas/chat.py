
#Schema request/response Chat
from typing import List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.answer import AnswerSource


class ChatRequest(BaseModel):
    """
    Request cho chức năng hỏi đáp lịch sử
    sử dụng RAG và GraphRAG.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Câu hỏi lịch sử của người dùng"
    )

    vector_top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Số lượng tài liệu truy xuất từ Vector Database"
    )

    graph_top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Số lượng kết quả truy xuất từ Knowledge Graph"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Câu hỏi không được để trống.")

        return value


class ChatResponse(BaseModel):
    """
    Response trả về từ hệ thống hỏi đáp.
    """

    query: str = Field(
        ...,
        description="Câu hỏi ban đầu của người dùng"
    )

    answer: str = Field(
        ...,
        description="Câu trả lời được sinh bởi hệ thống"
    )

    sources: List[AnswerSource] = Field(
        default_factory=list,
        description="Danh sách nguồn tài liệu hỗ trợ câu trả lời"
    )

    has_sufficient_context: bool = Field(
        default=False,
        description="Đánh giá mức độ đầy đủ của ngữ cảnh truy xuất"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Thông tin bổ sung về quá trình xử lý và truy xuất"
    )
