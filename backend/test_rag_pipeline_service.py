
from app.core.neo4j_connection import neo4j_connection
from app.services.rag_pipeline_service import rag_pipeline_service


def main():

    query = "Nguyễn Huệ có con hay không? Nếu có thì tên con là gì?"

    neo4j_connection.connect()

    print("\n===== START GRAPHRAG PIPELINE =====")

    result = rag_pipeline_service.run(
        query=query,
        vector_top_k=5,
        graph_top_k=5
    )

    # 1. Query Analysis
    print("\n===== QUERY ANALYSIS =====")
    print(result["analysis"])

    # 2. Retrieval
    print("\n===== RETRIEVAL =====")

    print(
        "Vector:",
        result["metadata"]["vector_retrieved"]
    )

    print(
        "Graph:",
        result["metadata"]["graph_retrieved"]
    )

    # 3. Context
    print("\n===== CONTEXT =====")

    print(
        "Vector Context:",
        len(result["context"]["vector_context"])
    )

    print(
        "Graph Context:",
        len(result["context"]["graph_context"])
    )

    # 4. Answer
    print("\n===== GENERATED ANSWER =====")

    answer = result["answer"]

    print("Question:", answer["query"])
    print("Answer:", answer["answer"])

    print(
        "Sufficient Context:",
        answer["has_sufficient_context"]
    )

    print("\n===== SOURCES =====")

    for source in answer["sources"]:
        print(
            f"Document: {source['document_name']} | "
            f"Page: {source['page_number']} | "
            f"Chunk: {source['chunk_id']}"
        )

    # 5. Metadata
    print("\n===== PIPELINE METADATA =====")
    print(result["metadata"])

    print("\n===== PIPELINE COMPLETED =====")


if __name__ == "__main__":
    main()
