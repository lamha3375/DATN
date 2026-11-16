
from typing import Any, Dict

from app.services.retrieval_service import retrieval_service
from app.services.context_builder_service import context_builder_service
from app.services.answer_generation_service import (
    answer_generation_service
)


class RAGPipelineService:

    def __init__(self):
        self.retrieval_service = retrieval_service
        self.context_builder_service = context_builder_service
        self.answer_generation_service = answer_generation_service

    def run(
        self,
        query: str,
        vector_top_k: int = 5,
        graph_top_k: int = 5
    ) -> Dict[str, Any]:

        query = query.strip() if query else ""

        if not query:
            raise ValueError("Câu hỏi không được để trống.")

        # 1. Retrieval
        retrieval_result = self.retrieval_service.retrieve(
            query=query,
            vector_top_k=vector_top_k,
            graph_top_k=graph_top_k
        )

        # 2. Context Building
        context_result = self.context_builder_service.build(
            retrieval_result
        )

        context = context_result.get("context", {})

        # 3. Answer Generation
        answer_result = self.answer_generation_service.generate(
            query=query,
            context=context
        )

        # 4. Tổng hợp kết quả
        return {
            "query": query,

            "analysis": retrieval_result.get("analysis", {}),

            "retrieval": retrieval_result.get("retrieval", {}),

            "context": context,

            "answer": answer_result.model_dump(),

            "metadata": {
                **context_result.get("metadata", {}),

                "vector_retrieved": (
                    retrieval_result
                    .get("retrieval", {})
                    .get("vector", {})
                    .get("count", 0)
                ),

                "graph_retrieved": (
                    retrieval_result
                    .get("retrieval", {})
                    .get("graph", {})
                    .get("count", 0)
                ),

                "answer_generated": bool(answer_result.answer),

                "has_sufficient_context": (
                    answer_result.has_sufficient_context
                )
            }
        }


rag_pipeline_service = RAGPipelineService()
