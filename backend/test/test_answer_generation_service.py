
from app.core.neo4j_connection import neo4j_connection
from app.services.rag_pipeline_service import rag_pipeline_service
from app.services.answer_generation_service import (
    answer_generation_service
)


def main():

    query = "1+1 = ?"

    neo4j_connection.connect()

    print("1. Đang chạy RAG Pipeline...")

    pipeline_result = rag_pipeline_service.run(
        query=query,
        vector_top_k=5,
        graph_top_k=5
    )

    print("2. Đang gửi Context đến Gemini...")

    answer_result = answer_generation_service.generate(
        query=query,
        context=pipeline_result["context"]
    )

    print("\n===== ANSWER RESULT =====")
    print(answer_result.model_dump_json(indent=2))

    print("\n===== ANSWER =====")
    print(answer_result.answer)

    print("\n===== SOURCES =====")

    for source in answer_result.sources:
        print(
            source.document_name,
            "| Page:", source.page_number
        )

    print("\n===== METADATA =====")
    print(
        "Sufficient context:",
        answer_result.has_sufficient_context
    )


if __name__ == "__main__":
    main()
