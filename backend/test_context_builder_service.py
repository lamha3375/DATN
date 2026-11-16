
from app.services.context_builder_service import (
    context_builder_service,
)


def create_mock_retrieval_result():
    return {
        "query": "Nguyễn Huệ đại phá quân Thanh năm nào?",

        "retrieval": {
            "vector": {
                "results": [
                    {
                        "chunk_id": "CHUNK_001",
                        "document_name": "Lịch sử Tây Sơn",
                        "page_number": 25,
                        "chunk_index": 1,
                        "content": "Nguyễn Huệ lên ngôi Hoàng đế năm 1788.",
                        "distance": 0.15,
                    },
                    {
                        "chunk_id": "CHUNK_002",
                        "document_name": "Lịch sử Tây Sơn",
                        "page_number": 26,
                        "chunk_index": 2,
                        "content": "Nguyễn Huệ đại phá quân Thanh vào năm 1789.",
                        "distance": 0.20,
                    },
                    {
                        "chunk_id": "CHUNK_003",
                        "document_name": "Lịch sử Tây Sơn",
                        "page_number": 26,
                        "chunk_index": 3,
                        "content": "Nguyễn Huệ đại phá quân Thanh vào năm 1789.",
                        "distance": 0.25,
                    },
                ],
            },

            "graph": {
                "results": [
                    {
                        "node_id": "123",
                        "labels": ["NhanVat"],
                        "properties": {
                            "name": "Nguyễn Huệ",
                            "title": "Quang Trung",
                            "birth_year": 1753,
                        },
                        "score": 10.5,
                        "matched_terms": ["nguyễn huệ"],

                        "relationships": [
                            {
                                "type": "CHI_HUY",
                                "direction": "outgoing",
                                "target": {
                                    "id": "456",
                                    "labels": ["SuKien"],
                                    "name": "Đại phá quân Thanh",
                                    "properties": {
                                        "year": 1789,
                                    },
                                },
                            }
                        ],
                    }
                ],
            },
        },
    }


def test_build_context():
    retrieval_result = create_mock_retrieval_result()

    result = context_builder_service.build(retrieval_result)

    assert result["query"] == retrieval_result["query"]

    assert "vector_context" in result["context"]
    assert "graph_context" in result["context"]
    assert "combined_context" in result["context"]

    assert result["metadata"]["vector_count"] == 2
    assert result["metadata"]["graph_count"] == 1

    assert "Nguyễn Huệ" in result["context"]["combined_context"]

    assert "1789" in result["context"]["combined_context"]

    print("\n===== CONTEXT BUILDER TEST =====")
    print("Vector count:", result["metadata"]["vector_count"])
    print("Graph count:", result["metadata"]["graph_count"])
    print(
        "Context length:",
        result["metadata"]["combined_context_length"],
    )
    print("\n===== COMBINED CONTEXT =====")
    print(result["context"]["combined_context"])


def test_empty_retrieval_results():
    retrieval_result = {
        "query": "Câu hỏi kiểm tra",
        "retrieval": {
            "vector": {"results": []},
            "graph": {"results": []},
        },
    }

    result = context_builder_service.build(retrieval_result)

    assert result["metadata"]["vector_count"] == 0
    assert result["metadata"]["graph_count"] == 0

    assert result["context"]["combined_context"]


def test_invalid_retrieval_result():
    try:
        context_builder_service.build({})
        assert False, "Phải phát sinh ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    test_build_context()
    test_empty_retrieval_results()
    test_invalid_retrieval_result()

    print("\nAll Context Builder tests passed.")
