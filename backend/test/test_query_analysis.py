
import pytest

from app.services.query_analysis_service import QueryAnalysisService


@pytest.fixture
def service():
    return QueryAnalysisService()


# ==========================================
# 1. CHARACTER QUERY
# ==========================================

@pytest.mark.parametrize("query", [
    "Nguyễn Huệ là ai?",
    "Tiểu sử của vua Quang Trung",
    "Nguyễn Nhạc có thân thế như thế nào?"
])
def test_character_query(service, query):
    result = service.analyze(query)

    assert result["intent"] == "character_query"


# ==========================================
# 2. EVENT QUERY
# ==========================================

@pytest.mark.parametrize("query", [
    "Trận Ngọc Hồi - Đống Đa diễn ra năm nào?",
    "Chiến thắng Rạch Gầm - Xoài Mút",
    "Phong trào Tây Sơn bùng nổ khi nào?",
    "Nguyễn Huệ tiến quân ra Bắc khi nào?"
])
def test_event_query(service, query):
    result = service.analyze(query)

    assert result["intent"] == "event_query"


# ==========================================
# 3. RELATIONSHIP QUERY
# ==========================================

@pytest.mark.parametrize("query", [
    "Nguyễn Huệ có quan hệ gì với Nguyễn Nhạc?",
    "Nguyễn Huệ là em của ai?",
    "Quan hệ gia đình của vua Quang Trung"
])
def test_relationship_query(service, query):
    result = service.analyze(query)

    assert result["intent"] == "relationship_query"


# ==========================================
# 4. REASONING QUERY
# ==========================================

@pytest.mark.parametrize("query", [
    "Vì sao phong trào Tây Sơn bùng nổ?",
    "Nguyên nhân dẫn đến chiến thắng Ngọc Hồi?",
    "Vai trò của Nguyễn Huệ trong phong trào Tây Sơn?",
    "Ý nghĩa của chiến thắng Rạch Gầm - Xoài Mút?"
])
def test_reasoning_query(service, query):
    result = service.analyze(query)

    assert result["intent"] == "reasoning_query"


# ==========================================
# 5. GENERAL QUERY
# ==========================================

@pytest.mark.parametrize("query", [
    "Tổng quan lịch sử Tây Sơn",
    "Lịch sử Tây Sơn",
    "Thông tin về phong trào Tây Sơn"
])
def test_general_query(service, query):
    result = service.analyze(query)

    assert result["intent"] == "general_query"


# ==========================================
# 6. QUERY NORMALIZATION
# ==========================================

def test_normalize_query(service):
    query = "  NGUYỄN   HUỆ   là ai?  "

    result = service.analyze(query)

    assert result["normalized_query"] == "nguyễn huệ là ai?"


def test_empty_query(service):
    with pytest.raises(ValueError):
        service.analyze("   ")


# ==========================================
# 7. KEYWORD EXTRACTION
# ==========================================

def test_extract_keywords(service):
    query = "Nguyễn Huệ đại phá quân Thanh"

    keywords = service.extract_keywords(query)

    assert "nguyễn" in keywords
    assert "huệ" in keywords
    assert "nguyễn huệ" in keywords
    assert "đại phá" in keywords
    assert "nguyễn huệ đại" in keywords


def test_keyword_extraction_does_not_merge_across_stopwords(service):
    query = "Nguyễn Huệ là vua Quang Trung"

    keywords = service.extract_keywords(query)

    assert "nguyễn huệ" in keywords
    assert "vua quang" not in keywords


# ==========================================
# 8. RETRIEVAL STRATEGY
# ==========================================

def test_relationship_strategy(service):
    result = service.analyze(
        "Nguyễn Huệ có quan hệ gì với Nguyễn Nhạc?"
    )

    strategy = result["retrieval_strategy"]

    assert strategy["vector_search"] is True
    assert strategy["graph_search"] is True
    assert strategy["relationship_expansion"] is True


def test_character_strategy(service):
    result = service.analyze("Nguyễn Huệ là ai?")

    strategy = result["retrieval_strategy"]

    assert strategy["vector_search"] is True
    assert strategy["graph_search"] is True
    assert strategy["relationship_expansion"] is False

#chạy từ thư mục gốc   
#python -m pytest backend/test_query_analysis.py -v