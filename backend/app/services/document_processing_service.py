
import logging
from typing import List, Set

from app.schemas.chunk import TextChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Điều phối quá trình:
    TextChunk -> Embedding -> ChromaDB.

    Nguyên tắc đồng bộ:
    1. Chỉ xử lý chunks thuộc cùng một tài liệu và phiên bản.
    2. Không embedding lại chunks đã tồn tại.
    3. Chỉ xóa chunks cũ sau khi chunks phiên bản mới
       đã được lưu và xác minh đầy đủ.
    4. Nếu xử lý thất bại, giữ nguyên chunks cũ.
    5. Không xóa dữ liệu khi danh sách chunks rỗng.
    """

    def __init__(self):

        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()

    # PROCESS DOCUMENT CHUNKS
    def process_chunks(
        self,
        chunks: List[TextChunk],
        finalize_document: bool = True
    ) -> dict:

        # 1. Không xử lý danh sách rỗng
        if not chunks:

            logger.warning(
                "Không có chunks để xử lý. "
                "Giữ nguyên dữ liệu hiện có trong ChromaDB."
            )

            return {
                "total_chunks": 0,
                "previously_stored": 0,
                "newly_stored": 0,
                "removed_stale_chunks": 0,
                "total_stored": (
                    self.vector_store_service.get_collection_count()
                ),
                "status": "skipped",
                "message": "Không có chunks. Không thực hiện đồng bộ."
            }

        # 2. Kiểm tra tính nhất quán của batch
        document_names = {
            chunk.document_name for chunk in chunks
        }

        document_ids = {
            chunk.document_id for chunk in chunks
        }

        content_hashes = {
            chunk.content_hash for chunk in chunks
        }

        if len(document_names) != 1:
            raise ValueError(
                "Một batch chỉ được chứa chunks của cùng một tài liệu."
            )

        if len(document_ids) != 1:
            raise ValueError(
                "Một batch chỉ được chứa chunks của cùng một document_id."
            )

        if len(content_hashes) != 1:
            raise ValueError(
                "Một batch không được trộn nhiều phiên bản content_hash."
            )

        document_id = next(iter(document_ids))
        document_name = next(iter(document_names))
        content_hash = next(iter(content_hashes))

        if not document_id or not document_id.strip():
            raise ValueError(
                "document_id không được để trống."
            )

        if not document_name or not document_name.strip():
            raise ValueError(
                "document_name không được để trống."
            )

        if not content_hash or not content_hash.strip():
            raise ValueError(
                "content_hash không được để trống."
            )

        # ----------------------------------------------
        # 3. Kiểm tra chunk_id
        # ----------------------------------------------

        chunk_ids = [
            chunk.chunk_id for chunk in chunks
        ]

        if any(not chunk_id for chunk_id in chunk_ids):
            raise ValueError(
                "Danh sách chunks chứa chunk_id rỗng."
            )

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError(
                "Danh sách chunks chứa chunk_id trùng lặp."
            )

        current_chunk_ids = set(chunk_ids)

        logger.info(
            "Bắt đầu xử lý PDF: %s | document_id=%s | "
            "content_hash=%s | total_chunks=%s",
            document_name,
            document_id,
            content_hash,
            len(chunks)
        )

        # ----------------------------------------------
        # 4. Tìm chunks đã tồn tại
        # ----------------------------------------------

        existing_ids = (
            self.vector_store_service.get_existing_ids(
                chunk_ids
            )
        )

        pending_chunks = [
            chunk
            for chunk in chunks
            if chunk.chunk_id not in existing_ids
        ]

        previously_stored = len(existing_ids)
        newly_stored = 0

        logger.info(
            "PDF %s: %s chunks đã tồn tại, "
            "%s chunks cần embedding.",
            document_name,
            previously_stored,
            len(pending_chunks)
        )

        # 5. Embedding và lưu chunks mới
        if pending_chunks:

            for batch_embeddings in (
                self.embedding_service.embed_chunks_in_batches(
                    pending_chunks
                )
            ):

                if not batch_embeddings:
                    continue

                stored_count = (
                    self.vector_store_service.store_embeddings_batch(
                        batch_embeddings
                    )
                )

                newly_stored += stored_count

                logger.info(
                    "PDF %s: đã lưu %s/%s chunks mới.",
                    document_name,
                    newly_stored,
                    len(pending_chunks)
                )

            # Không cho phép pipeline âm thầm bỏ sót chunks.
            if newly_stored != len(pending_chunks):

                logger.error(
                    "Số chunks lưu không khớp: cần %s, đã lưu %s.",
                    len(pending_chunks),
                    newly_stored
                )

                raise RuntimeError(
                    "Embedding/lưu ChromaDB chưa hoàn tất. "
                    "Giữ nguyên chunks cũ."
                )

        # ----------------------------------------------
        # 6. Xác minh phiên bản mới đã được lưu đầy đủ
        # ----------------------------------------------

        persisted_ids = (
            self.vector_store_service.get_existing_ids(
                chunk_ids
            )
        )

        missing_ids = current_chunk_ids - persisted_ids

        if missing_ids:

            logger.error(
                "PDF %s còn thiếu %s chunks sau khi lưu.",
                document_name,
                len(missing_ids)
            )

            raise RuntimeError(
                f"ChromaDB còn thiếu {len(missing_ids)} chunks. "
                "Không dọn dữ liệu phiên bản cũ."
            )

        # ----------------------------------------------
        # 7. Chỉ dọn chunks cũ khi đã xác minh thành công
        # ----------------------------------------------

        removed_stale = 0

        if finalize_document:

            removed_stale = self.finalize_document(
                document_id=document_id,
                current_chunk_ids=current_chunk_ids
            )

        total_stored = (
            self.vector_store_service.get_collection_count()
        )

        logger.info(
            "Hoàn tất PDF: %s | total=%s | existing=%s | "
            "new=%s | removed_stale=%s",
            document_name,
            len(chunks),
            previously_stored,
            newly_stored,
            removed_stale
        )

        return {
            "document_id": document_id,
            "document_name": document_name,
            "content_hash": content_hash,
            "total_chunks": len(chunks),
            "previously_stored": previously_stored,
            "newly_stored": newly_stored,
            "removed_stale_chunks": removed_stale,
            "total_stored": total_stored,
            "status": "success"
        }

    # ==================================================
    # FINALIZE DOCUMENT
    # ==================================================

    def finalize_document(
        self,
        document_id: str,
        current_chunk_ids: Set[str]
    ) -> int:

        if not document_id:
            raise ValueError(
                "document_id không được để trống."
            )

        if not current_chunk_ids:
            logger.warning(
                "Không thực hiện finalize cho %s vì "
                "current_chunk_ids rỗng.",
                document_id
            )
            return 0

        # 1. Xác minh chunks hiện tại thực sự tồn tại
        persisted_ids = (
            self.vector_store_service.get_existing_ids(
                sorted(current_chunk_ids)
            )
        )

        missing_ids = current_chunk_ids - persisted_ids

        if missing_ids:
            raise RuntimeError(
                f"Không thể finalize {document_id}: "
                f"còn thiếu {len(missing_ids)} chunks hiện tại."
            )

        # 2. Lấy toàn bộ chunks của tài liệu
        previous_ids = (
            self.vector_store_service.get_document_chunk_ids(
                document_id
            )
        )

        # 3. Xác định chunks không còn thuộc phiên bản mới
        stale_ids = previous_ids - current_chunk_ids

        if not stale_ids:
            logger.info(
                "PDF %s không có chunks cũ cần dọn.",
                document_id
            )
            return 0

        # 4. Xóa chunks cũ
        removed_count = (
            self.vector_store_service.delete_ids(
                sorted(stale_ids)
            )
        )

        logger.info(
            "Đã dọn %s chunks cũ của tài liệu %s.",
            removed_count,
            document_id
        )

        return removed_count
