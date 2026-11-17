
from app.schemas.answer import AnswerResponse, AnswerSource


def test_answer_schema():

    result = AnswerResponse(
        query="Nguyễn Huệ đại phá quân Thanh năm nào?",
        answer="Năm 1789.",
        sources=[
            AnswerSource(
                document_name="Hoàng Lê nhất thống chí",
                page_number=120,
                chunk_id="CHUNK_001"
            )
        ],
        has_sufficient_context=True
    )

    assert result.query
    assert result.answer == "Năm 1789."
    assert len(result.sources) == 1
    assert result.has_sufficient_context is True

    print(result.model_dump())


def test_empty_sources():

    result = AnswerResponse(
        query="Một câu hỏi lịch sử",
        answer="Chưa đủ dữ liệu để trả lời."
    )

    assert result.sources == []
    assert result.has_sufficient_context is False
