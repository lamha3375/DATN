
import logging
from typing import List

from app.schemas.chunk import TextChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


class DocumentProcessingService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()

    def process_chunks(
        self,
        chunks: List[TextChunk]
    ) -> dict:

        if not chunks:
            raise ValueError("Danh sách chunks không được để trống.")

        total_chunks = len(chunks)

        # 1. Kiểm tra chunks đã tồn tại
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        existing_ids = self.vector_store_service.get_existing_ids(
            chunk_ids
        )

        # 2. Chỉ lấy chunks chưa được lưu
        pending_chunks = [
            chunk for chunk in chunks
            if chunk.chunk_id not in existing_ids
        ]

        skipped_chunks = total_chunks - len(pending_chunks)

        logger.info(
            "Tổng chunks: %s | Đã có: %s | Chờ xử lý: %s",
            total_chunks,
            skipped_chunks,
            len(pending_chunks)
        )

        processed_chunks = 0

        # 3. Embedding theo batch và lưu ngay vào ChromaDB
        for batch_embeddings in self.embedding_service.embed_chunks_in_batches(
            pending_chunks
        ):

            stored = self.vector_store_service.store_embeddings_batch(
                batch_embeddings
            )

            processed_chunks += stored

            logger.info(
                "Tiến độ: %s/%s chunks mới được lưu",
                processed_chunks,
                len(pending_chunks)
            )

        # 4. Trả kết quả
        return {
            "total_chunks": total_chunks,
            "previously_stored": skipped_chunks,
            "newly_stored": processed_chunks,
            "total_stored": self.vector_store_service.get_collection_count(),
            "status": "success"
        }
