
import pytest
import json

from app.core.neo4j_connection import neo4j_connection
from app.services.retrieval_service import retrieval_service


# =====================================================
# TEST CASES
# =====================================================

TEST_QUERIES = [
    {
        "name": "Character Query",
        "query": "Nguyễn Huệ là ai?",
        "expected_intent": "character_query",
        "expected_expansion": False,
    },
    {
        "name": "Event Query",
        "query": "Trận Ngọc Hồi diễn ra năm nào?",
        "expected_intent": "event_query",
        "expected_expansion": True,
    },
    {
        "name": "Relationship Query",
        "query": "Nguyễn Huệ có quan hệ gì với Nguyễn Nhạc?",
        "expected_intent": "relationship_query",
        "expected_expansion": True,
    },
    {
        "name": "Reasoning Query",
        "query": "Vì sao phong trào Tây Sơn bùng nổ?",
        "expected_intent": "reasoning_query",
        "expected_expansion": True,
    },
]


# =====================================================
# HELPER: PRINT GRAPH DETAILS
# =====================================================

def print_graph_details(graph_results):

    print("\n===== GRAPH RETRIEVAL DETAILS =====")

    if not graph_results:
        print("Không tìm thấy kết quả Graph.")
        return

    for index, item in enumerate(graph_results, start=1):

        print(f"\n--- NODE {index} ---")

        print("Node ID:", item.get("node_id"))
        print("Labels:", item.get("labels"))

        print(
            "Properties:",
            json.dumps(
                item.get("properties", {}),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        )

        print("Score:", item.get("score"))
        print("Matched terms:", item.get("matched_terms"))

        print(
            "Relationships:",
            json.dumps(
                item.get("relationships", []),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        )


# =====================================================
# FIXTURE: NEO4J CONNECTION
# =====================================================

@pytest.fixture(scope="module", autouse=True)
def setup_neo4j():

    neo4j_connection.connect()

    yield

    # Đóng kết nối sau khi toàn bộ test hoàn thành.
    # Chỉ gọi close nếu connection class có hỗ trợ.
    if hasattr(neo4j_connection, "close"):
        neo4j_connection.close()


# =====================================================
# INTEGRATION TEST
# =====================================================

@pytest.mark.parametrize(
    "test_case",
    TEST_QUERIES,
    ids=[case["name"] for case in TEST_QUERIES],
)
def test_retrieval_service(test_case):

    query = test_case["query"]

    result = retrieval_service.retrieve(
        query=query,
        vector_top_k=5,
        graph_top_k=5,
    )

    # ---------------------------------------------
    # 1. CHECK RESPONSE STRUCTURE
    # ---------------------------------------------

    assert isinstance(result, dict)

    assert "analysis" in result
    assert "retrieval" in result

    retrieval = result["retrieval"]

    assert "vector" in retrieval
    assert "graph" in retrieval

    # ---------------------------------------------
    # 2. CHECK QUERY ANALYSIS
    # ---------------------------------------------

    analysis = result["analysis"]

    assert analysis["intent"] == test_case["expected_intent"]

    assert isinstance(analysis["keywords"], list)

    strategy = analysis["retrieval_strategy"]

    assert strategy["vector_search"] is True
    assert strategy["graph_search"] is True

    assert (
        strategy["relationship_expansion"]
        == test_case["expected_expansion"]
    )

    # ---------------------------------------------
    # 3. CHECK VECTOR RETRIEVAL
    # ---------------------------------------------

    vector = retrieval["vector"]

    assert isinstance(vector["results"], list)

    assert vector["count"] == len(vector["results"])

    # ---------------------------------------------
    # 4. CHECK GRAPH RETRIEVAL
    # ---------------------------------------------

    graph = retrieval["graph"]

    assert isinstance(graph["results"], list)

    assert graph["count"] == len(graph["results"])

    for item in graph["results"]:

        assert "node_id" in item
        assert "labels" in item
        assert "properties" in item
        assert "score" in item
        assert "matched_terms" in item
        assert "relationships" in item

        assert isinstance(item["relationships"], list)

        # Character query không mở rộng quan hệ.
        if not test_case["expected_expansion"]:
            assert item["relationships"] == []

    # ---------------------------------------------
    # 5. PRINT DIAGNOSTIC INFORMATION
    # ---------------------------------------------

    print("\n" + "=" * 70)

    print("TEST:", test_case["name"])
    print("QUERY:", query)
    print("INTENT:", analysis["intent"])
    print("KEYWORDS:", analysis["keywords"])

    print(
        "RELATIONSHIP EXPANSION:",
        strategy["relationship_expansion"],
    )

    print("VECTOR RESULTS:", vector["count"])
    print("GRAPH RESULTS:", graph["count"])

    total_relationships = sum(
        len(item["relationships"])
        for item in graph["results"]
    )

    print("TOTAL RELATIONSHIPS:", total_relationships)

    # In chi tiết từng node Graph.
    print_graph_details(graph["results"])

    print("=" * 70)


# =====================================================
# MAIN: RUN WITHOUT PYTEST
# =====================================================

def main():

    print("\n" + "#" * 70)
    print("START RETRIEVAL SERVICE TESTING")
    print("#" * 70)

    neo4j_connection.connect()

    try:

        for case in TEST_QUERIES:

            print("\n" + "=" * 70)
            print("TEST:", case["name"])
            print("QUERY:", case["query"])

            result = retrieval_service.retrieve(
                query=case["query"],
                vector_top_k=5,
                graph_top_k=5,
            )

            analysis = result["analysis"]
            retrieval = result["retrieval"]

            print("\n--- QUERY ANALYSIS ---")

            print("Intent:", analysis["intent"])
            print("Keywords:", analysis["keywords"])

            print(
                "Retrieval Strategy:",
                json.dumps(
                    analysis["retrieval_strategy"],
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            print("\n--- VECTOR RETRIEVAL ---")

            vector = retrieval["vector"]

            print("Vector count:", vector["count"])

            print("\n--- GRAPH RETRIEVAL ---")

            graph = retrieval["graph"]

            print("Graph count:", graph["count"])

            print_graph_details(graph["results"])

            print("=" * 70)

    finally:

        if hasattr(neo4j_connection, "close"):
            neo4j_connection.close()

        print("\nRETRIEVAL TESTING COMPLETED.")


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    main()
