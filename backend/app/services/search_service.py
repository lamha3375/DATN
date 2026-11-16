
from typing import List

from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem
)


class SearchService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()

    def search(self, request: SearchRequest) -> SearchResponse:

        query = request.query.strip()

        if not query:
            raise ValueError("Câu truy vấn không được để trống.")

        # 1. Chuyển câu hỏi thành embedding
        query_embedding = self.embedding_service.embed_query(query)

        # 2. Tìm kiếm các chunks liên quan trong ChromaDB
        search_results = self.vector_store_service.search(
            query_embedding=query_embedding,
            top_k=request.top_k
        )

        # 3. Chuyển kết quả sang schema
        results: List[SearchResultItem] = [
            SearchResultItem(**item)
            for item in search_results
        ]

        # 4. Trả về kết quả
        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results
        )
# Hiện tại SearchService đang khởi tạo một EmbeddingService riêng. 
# Vì model được tải theo cơ chế lazy loading nên chưa phát sinh việc tải model ngay khi tạo đối tượng. 
# Tuy nhiên, nếu nhiều service cùng sử dụng model, về sau ta nên quản lý một instance dùng chung để tránh tiêu tốn RAM không cần thiết.